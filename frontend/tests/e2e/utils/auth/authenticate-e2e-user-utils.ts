/**
 * E2E auth entry point for the frontend Playwright suite.
 * Reviewer conclusion:
 * - the auth behavior is unchanged (same staging/local branching),
 *   but failures now include structured triage context.
 *
 * Reliability hardening note:
 * - all raised auth-flow failures now include error time, failed step,
 *   what to inspect, and likely root cause.
 *
 * The test suite supports two real login paths:
 * - local: fetch a JWT from the app's internal API and create a spoofed client session
 * - staging: open the deployed frontend, click Sign in, and submit the seeded API key in the modal
 *
 * The app only has seeded test users and no normal login credentials for E2E, so the suite
 * fails fast when required environment values are missing.
 */

import { type BrowserContext, type Page } from "@playwright/test";
import playwrightEnv from "tests/e2e/playwright-env";
import { openMobileNav } from "tests/e2e/playwrightUtils";
import { createSpoofedSessionCookie } from "tests/e2e/utils/auth/login-utils";
import {
  getTestUserId,
  type TestUserKey,
} from "tests/e2e/utils/auth/test-users";

const { baseUrl, apiUrl } = playwrightEnv;

const TEMPORARY_MODAL_HOST_PREFIXES = ["frontend-dev-", "frontend-staging-"];
const TEMPORARY_MODAL_HOST_SUFFIX = ".us-east-1.elb.amazonaws.com";
const TEMPORARY_MODAL_LOGIN_TIMEOUT_MS = 60_000;
const AUTH_FLOW_NAME = "frontend-e2e-auth";

const isTemporaryModalHost = (hostname: string): boolean =>
  TEMPORARY_MODAL_HOST_PREFIXES.some((prefix) => hostname.startsWith(prefix)) &&
  hostname.endsWith(TEMPORARY_MODAL_HOST_SUFFIX);

const effectiveTemporaryModalBaseUrl = (() => {
  try {
    const parsedUrl = new URL(baseUrl);
    if (
      isTemporaryModalHost(parsedUrl.hostname) &&
      parsedUrl.protocol === "https:"
    ) {
      parsedUrl.protocol = "http:";
      return parsedUrl.toString();
    }
  } catch {
    return baseUrl;
  }

  return baseUrl;
})();

const getMissingStagingApiKeyErrorMessage = ({
  targetEnv,
  baseUrl: currentBaseUrl,
}: {
  targetEnv: string;
  baseUrl: string;
}): string =>
  [
    "Missing required E2E API key for the deployed frontend login flow.",
    `Target environment: ${targetEnv || "unknown"}.`,
    `Base URL: ${currentBaseUrl || "unknown"}.`,
    "The run cannot continue until one of these values is populated:",
    "- STAGING_TEST_USER_API_KEY (GitHub Actions secret) mapped to TEST_USER_API_KEY",
    "- TEST_USER_API_KEY set in the workflow env",
    "This is the active staging sign-in flow for the E2E suite.",
  ].join("\n");

const getErrorCauseMessage = (error: unknown): string => {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return String(error);
};

const buildAuthStepErrorMessage = ({
  step,
  inspect,
  likelyCause,
  details,
  error,
}: {
  step: string;
  inspect: string;
  likelyCause: string;
  details: string;
  error?: unknown;
}): string =>
  [
    `Error time (UTC): ${new Date().toISOString()}`,
    `Flow: ${AUTH_FLOW_NAME}`,
    `Failed step: ${step}`,
    `What to inspect: ${inspect}`,
    `Likely cause: ${likelyCause}`,
    `Target environment: ${playwrightEnv.targetEnv || "unknown"}`,
    `Base URL: ${baseUrl || "unset"}`,
    `API URL: ${apiUrl || "unset"}`,
    details,
    error ? `Original error: ${getErrorCauseMessage(error)}` : null,
  ]
    .filter(Boolean)
    .join("\n");

const createAuthStepError = ({
  step,
  inspect,
  likelyCause,
  details,
  error,
}: {
  step: string;
  inspect: string;
  likelyCause: string;
  details: string;
  error?: unknown;
}): Error =>
  // Keep all auth failures in one normalized shape so CI logs are easier to scan.
  new Error(
    buildAuthStepErrorMessage({ step, inspect, likelyCause, details, error }),
  );

const isTemporaryApiKeyModalFlow = (): boolean => {
  try {
    const { hostname } = new URL(baseUrl);
    return isTemporaryModalHost(hostname);
  } catch {
    return false;
  }
};

const clickTemporaryApiKeySignInTrigger = async (page: Page) => {
  const candidateTriggers = [
    page.getByRole("button", { name: /open login modal/i }).first(),
    page.getByRole("button", { name: /sign in/i }).first(),
    page.getByRole("link", { name: /sign in/i }).first(),
  ];

  for (const trigger of candidateTriggers) {
    const isVisible = await trigger.isVisible({ timeout: 3000 }).catch(() => {
      return false;
    });

    if (isVisible) {
      await trigger.click();
      return;
    }
  }

  throw createAuthStepError({
    step: "open-staging-sign-in-trigger",
    inspect:
      "deployed page content, Sign in button selectors, and auth entrypoint visibility",
    likelyCause: "staging UI changed or page failed to fully load",
    details:
      "The staging API-key modal did not open because no visible Sign in trigger was found.",
  });
};

const getMaskedApiKey = (apiKey: string): string =>
  apiKey ? `${apiKey.slice(0, 4)}...${apiKey.slice(-4)}` : "empty";

const throwMissingRequiredValueError = ({
  step,
  missingValues,
  inspect,
  likelyCause,
  additionalDetails,
}: {
  step: string;
  missingValues: string[];
  inspect: string;
  likelyCause: string;
  additionalDetails?: string;
}) => {
  const missingList = missingValues.join(", ");
  // Missing prerequisites are treated as hard failures to stop invalid test runs early.
  throw createAuthStepError({
    step,
    inspect,
    likelyCause,
    details: [
      `Missing required values: ${missingList}.`,
      additionalDetails || null,
    ]
      .filter(Boolean)
      .join("\n"),
  });
};

const waitForTemporaryApiKeyModalReady = async (page: Page) => {
  const apiKeyInput = page.locator('input[name="apiKey"]').first();

  for (let attempt = 0; attempt < 5; attempt += 1) {
    const inputVisible = await apiKeyInput.isVisible().catch(() => false);
    if (inputVisible) {
      return apiKeyInput;
    }

    // Retry sign-in trigger clicks because staging UI timing can vary.
    await clickTemporaryApiKeySignInTrigger(page);
    await page.waitForTimeout(800);
  }

  throw createAuthStepError({
    step: "wait-for-staging-api-key-modal",
    inspect:
      "sign-in modal selector, login button behavior, and page interactivity",
    likelyCause: "modal trigger did not fire or frontend rendering was delayed",
    details: [
      "The staging API-key modal did not open after the Sign in button was clicked.",
      `Effective staging base URL: ${effectiveTemporaryModalBaseUrl}.`,
    ].join("\n"),
  });
};

const isAnySignInTriggerVisible = async (page: Page): Promise<boolean> => {
  const triggerLocators = [
    page.getByRole("button", { name: /open login modal/i }).first(),
    page.getByRole("button", { name: /sign in/i }).first(),
    page.getByRole("link", { name: /sign in/i }).first(),
  ];

  for (const locator of triggerLocators) {
    const visible = await locator.isVisible().catch(() => false);
    if (visible) {
      return true;
    }
  }

  return false;
};

const waitForTemporaryApiKeyModalLoginState = async (page: Page) => {
  const startedAt = Date.now();
  const invalidApiKeyAlert = page
    .getByRole("alert")
    .filter({ hasText: /invalid api key/i })
    .first();
  const authenticatedMarker = page
    .locator(
      'button[aria-controls="Account"], [data-testid="user-menu-trigger"], a:has-text("Sign out"), button:has-text("Sign out")',
    )
    .first();
  const loginHeading = page.getByRole("heading", {
    name: /login with api key/i,
  });

  while (Date.now() - startedAt < TEMPORARY_MODAL_LOGIN_TIMEOUT_MS) {
    if (await invalidApiKeyAlert.isVisible().catch(() => false)) {
      throw createAuthStepError({
        step: "submit-staging-api-key",
        inspect:
          "staging TEST_USER_API_KEY secret mapping and host/environment pairing",
        likelyCause: "API key does not match the deployed staging host",
        details: [
          "The staging login failed because the UI returned an invalid API key message.",
          "Use a valid TEST_USER_API_KEY for this host.",
        ].join("\n"),
      });
    }

    if (await authenticatedMarker.isVisible().catch(() => false)) {
      return;
    }

    const signInVisible = await isAnySignInTriggerVisible(page);
    const loginModalVisible = await loginHeading.isVisible().catch(() => false);
    // If neither sign-in trigger nor modal is visible, assume auth completed.
    if (!signInVisible && !loginModalVisible) {
      return;
    }

    await page.waitForTimeout(500);
  }

  throw createAuthStepError({
    step: "wait-for-staging-authenticated-state",
    inspect:
      "post-login redirects, auth marker selectors, and modal close state",
    likelyCause:
      "session was not established or auth UI state did not transition",
    details: [
      "The staging sign-in flow timed out before the user was marked as authenticated.",
      `Effective staging base URL: ${effectiveTemporaryModalBaseUrl}.`,
    ].join("\n"),
  });
};

const authenticateWithTemporaryApiKeyModal = async (
  page: Page,
  isMobile: boolean,
  testUserApiKeyOverride: string,
) => {
  const apiKey = testUserApiKeyOverride;

  if (!apiKey) {
    throw createAuthStepError({
      step: "load-staging-api-key",
      inspect: "workflow secrets and TEST_USER_API_KEY environment mapping",
      likelyCause:
        "staging API key secret is unset or not forwarded to Playwright",
      details: getMissingStagingApiKeyErrorMessage({
        targetEnv: playwrightEnv.targetEnv,
        baseUrl: effectiveTemporaryModalBaseUrl,
      }),
    });
  }

  try {
    await page.goto(effectiveTemporaryModalBaseUrl, {
      waitUntil: "domcontentloaded",
    });
  } catch (error) {
    throw createAuthStepError({
      step: "navigate-to-staging-app",
      inspect:
        "PLAYWRIGHT_BASE_URL, deployment health, and network availability",
      likelyCause: "deployed frontend URL is unreachable or misconfigured",
      details: `Unable to navigate to ${effectiveTemporaryModalBaseUrl}.`,
      error,
    });
  }

  if (isMobile) {
    try {
      await openMobileNav(page);
    } catch (error) {
      throw createAuthStepError({
        step: "open-mobile-navigation-before-sign-in",
        inspect: "mobile nav selectors and viewport-dependent menu behavior",
        likelyCause:
          "mobile nav trigger changed or page is not fully interactive",
        details: "Failed while opening mobile navigation before sign-in.",
        error,
      });
    }
  }

  const apiKeyInput = await waitForTemporaryApiKeyModalReady(page);
  try {
    await apiKeyInput.fill(apiKey);
  } catch (error) {
    throw createAuthStepError({
      step: "fill-staging-api-key-field",
      inspect: "apiKey input selector and modal readiness",
      likelyCause: "modal input was not ready or was replaced during rerender",
      details: "Unable to fill the API key input in the staging sign-in modal.",
      error,
    });
  }

  const loginButton = page.getByRole("button", { name: /^login$/i }).first();
  try {
    await loginButton.waitFor({
      state: "visible",
      timeout: TEMPORARY_MODAL_LOGIN_TIMEOUT_MS,
    });
    await loginButton.click();
  } catch (error) {
    throw createAuthStepError({
      step: "submit-staging-api-key-login",
      inspect: "Login button selector and modal submit behavior",
      likelyCause:
        "Login button is not visible/clickable or modal failed to mount",
      details: "Unable to submit the staging API-key login form.",
      error,
    });
  }

  await waitForTemporaryApiKeyModalLoginState(page);
};

export const fetchE2eSessionToken = async (
  testUserApiKey: string,
): Promise<string> => {
  const maskedTestUserApiKey = getMaskedApiKey(testUserApiKey);

  if (!testUserApiKey || !apiUrl) {
    const missingConfig = [
      !testUserApiKey ? "TEST_USER_API_KEY" : null,
      !apiUrl ? "PLAYWRIGHT_API_URL" : null,
    ].filter(Boolean) as string[];

    throwMissingRequiredValueError({
      step: "validate-token-fetch-prerequisites",
      missingValues: missingConfig,
      inspect:
        "PLAYWRIGHT_API_URL, TEST_USER_API_KEY, and CI secret wiring for STAGING_TEST_USER_API_KEY",
      likelyCause:
        "required environment variables were not populated before test run",
      additionalDetails: [
        "Unable to fetch the E2E session token.",
        "For staging in CI, set STAGING_API_URL and STAGING_TEST_USER_API_KEY before the Playwright run begins.",
        `Current PLAYWRIGHT_API_URL: ${apiUrl || "unset"}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
      ].join("\n"),
    });
  }

  const requestUrl = `${apiUrl}/v1/internal/api-jwt`;
  let response: Response;
  try {
    response = await fetch(requestUrl, {
      headers: {
        "X-API-Key": testUserApiKey,
        "Content-Type": "application/json",
      },
      method: "GET",
    });
  } catch (error) {
    throw createAuthStepError({
      step: "request-e2e-session-token",
      inspect:
        "PLAYWRIGHT_API_URL connectivity and /v1/internal/api-jwt availability",
      likelyCause: "API host is unreachable or network request failed",
      details: `Network request to ${requestUrl} failed while fetching the E2E session token.`,
      error,
    });
  }

  if (!response.ok) {
    const responseBody = await response.text();
    const responseHint =
      response.status === 404
        ? "Check that the deployed API is exposing GET /v1/internal/api-jwt and that PLAYWRIGHT_API_URL points to the correct host."
        : "Check that the API key is valid for this environment.";

    throw createAuthStepError({
      step: "validate-e2e-session-token-response",
      inspect:
        "API response status/body and API-key permissions for the target host",
      likelyCause:
        "token endpoint rejected the request or host does not expose endpoint",
      details: [
        `Unable to fetch the E2E session token. Status: ${response.status}.`,
        `Request URL: ${requestUrl}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
        responseBody
          ? `Response body: ${responseBody}`
          : "Response body: empty.",
        responseHint,
      ].join("\n"),
    });
  }

  let json: { data: { jwt_token: string } };
  try {
    json = (await response.json()) as { data: { jwt_token: string } };
  } catch (error) {
    throw createAuthStepError({
      step: "parse-e2e-session-token-response",
      inspect: "response JSON shape from /v1/internal/api-jwt",
      likelyCause: "endpoint response body is not valid JSON",
      details:
        "Received a non-JSON response while parsing the E2E session token payload.",
      error,
    });
  }

  if (!json?.data?.jwt_token) {
    throw createAuthStepError({
      step: "validate-e2e-session-token-payload",
      inspect: "jwt_token field in response payload from /v1/internal/api-jwt",
      likelyCause: "API returned an unexpected payload schema",
      details:
        "Response JSON is missing data.jwt_token, so session setup cannot continue.",
    });
  }

  return json.data.jwt_token;
};

export async function authenticateE2eUser(
  page: Page,
  context: BrowserContext,
  isMobile: boolean,
  testUserKey: TestUserKey = "primaryOrgAdmin",
  testUserApiKeyOverride: string = playwrightEnv.testUserApiKey,
): Promise<void> {
  const maskedTestUserApiKey = getMaskedApiKey(testUserApiKeyOverride);

  if (playwrightEnv.targetEnv === "staging") {
    if (!testUserApiKeyOverride) {
      throw createAuthStepError({
        step: "validate-staging-prerequisites",
        inspect:
          "STAGING_TEST_USER_API_KEY secret and TEST_USER_API_KEY workflow mapping",
        likelyCause:
          "staging key was not injected into the Playwright environment",
        details: [
          "Unable to log in to staging: the E2E API key is missing.",
          "Set STAGING_TEST_USER_API_KEY and pass it through to TEST_USER_API_KEY for the run.",
          `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
        ].join("\n"),
      });
    }

    await authenticateWithTemporaryApiKeyModal(
      page,
      isMobile,
      testUserApiKeyOverride,
    );
    return;
  }

  if (!testUserApiKeyOverride || !apiUrl) {
    const missingConfig = [
      !testUserApiKeyOverride ? "TEST_USER_API_KEY" : null,
      !apiUrl ? "PLAYWRIGHT_API_URL" : null,
    ].filter(Boolean) as string[];

    throwMissingRequiredValueError({
      step: "validate-local-prerequisites",
      missingValues: missingConfig,
      inspect:
        "PLAYWRIGHT_API_URL and TEST_USER_API_KEY setup for local login spoof flow",
      likelyCause:
        "local E2E environment variables are missing or test bootstrap did not export them",
      additionalDetails: [
        `Unable to create the local E2E session for ${playwrightEnv.targetEnv || "unknown"}.`,
        `Current PLAYWRIGHT_API_URL: ${apiUrl || "unset"}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
      ].join("\n"),
    });
  }

  const userId = getTestUserId(testUserKey);
  // Validate requested seeded-user key before token fetch; the token endpoint remains API-key based.
  void userId;
  const token = await fetchE2eSessionToken(testUserApiKeyOverride);
  try {
    await createSpoofedSessionCookie(context, token);
  } catch (error) {
    throw createAuthStepError({
      step: "create-local-spoofed-session-cookie",
      inspect: "SESSION_SECRET values and spoofed cookie generation logic",
      likelyCause: "client session secret is missing or token signing failed",
      details: "Unable to create the spoofed local E2E session cookie.",
      error,
    });
  }

  const preNavWait = isMobile ? 2000 : 1000;
  const postNavWait = isMobile ? 4000 : 2000;
  await page.waitForTimeout(preNavWait);
  try {
    await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
  } catch (error) {
    throw createAuthStepError({
      step: "navigate-to-local-app-after-auth",
      inspect: "PLAYWRIGHT_BASE_URL and local frontend availability",
      likelyCause: "frontend host is unavailable or base URL is incorrect",
      details: `Unable to navigate to local app URL ${baseUrl}.`,
      error,
    });
  }
  await page.waitForTimeout(postNavWait);
}

export { isTemporaryApiKeyModalFlow };

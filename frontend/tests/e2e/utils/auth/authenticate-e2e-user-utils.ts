/**
 * E2E auth entry point for the frontend Playwright suite.
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
    const isVisible = await trigger
      .isVisible({ timeout: 3000 })
      .catch(() => false);

    if (isVisible) {
      await trigger.click();
      return;
    }
  }

  throw new Error(
    "The staging API-key modal did not open: no visible Sign in trigger was found.",
  );
};

const waitForTemporaryApiKeyModalReady = async (page: Page) => {
  const apiKeyInput = page.locator('input[name="apiKey"]').first();

  for (let attempt = 0; attempt < 5; attempt += 1) {
    const inputVisible = await apiKeyInput.isVisible().catch(() => false);
    if (inputVisible) {
      return apiKeyInput;
    }

    await clickTemporaryApiKeySignInTrigger(page);
    await page.waitForTimeout(800);
  }

  throw new Error(
    [
      "The staging API-key modal did not open after the Sign in button was clicked.",
      `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
      `Base URL: ${effectiveTemporaryModalBaseUrl}.`,
    ].join("\n"),
  );
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
      throw new Error(
        [
          "The staging login failed: the UI returned an invalid API key message.",
          `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
          `Base URL: ${effectiveTemporaryModalBaseUrl}.`,
          "Use a valid TEST_USER_API_KEY for this host.",
        ].join("\n"),
      );
    }

    if (await authenticatedMarker.isVisible().catch(() => false)) {
      return;
    }

    const signInVisible = await isAnySignInTriggerVisible(page);
    const loginModalVisible = await loginHeading.isVisible().catch(() => false);
    if (!signInVisible && !loginModalVisible) {
      return;
    }

    await page.waitForTimeout(500);
  }

  throw new Error(
    [
      "The staging sign-in flow timed out before the user was marked as authenticated.",
      `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
      `Base URL: ${effectiveTemporaryModalBaseUrl}.`,
    ].join("\n"),
  );
};

const authenticateWithTemporaryApiKeyModal = async (
  page: Page,
  isMobile: boolean,
) => {
  const apiKey = playwrightEnv.testUserApiKey;

  if (!apiKey) {
    throw new Error(
      getMissingStagingApiKeyErrorMessage({
        targetEnv: playwrightEnv.targetEnv,
        baseUrl: effectiveTemporaryModalBaseUrl,
      }),
    );
  }

  await page.goto(effectiveTemporaryModalBaseUrl, {
    waitUntil: "domcontentloaded",
  });

  if (isMobile) {
    await openMobileNav(page);
  }

  const apiKeyInput = await waitForTemporaryApiKeyModalReady(page);
  await apiKeyInput.fill(apiKey);

  const loginButton = page.getByRole("button", { name: /^login$/i }).first();
  await loginButton.waitFor({
    state: "visible",
    timeout: TEMPORARY_MODAL_LOGIN_TIMEOUT_MS,
  });
  await loginButton.click();

  await waitForTemporaryApiKeyModalLoginState(page);
};

export const fetchE2eSessionToken = async (
  testUserApiKey: string,
): Promise<string> => {
  const maskedTestUserApiKey = testUserApiKey
    ? `${testUserApiKey.slice(0, 4)}...${testUserApiKey.slice(-4)}`
    : "empty";

  if (!testUserApiKey || !apiUrl) {
    const missingConfig = [
      !testUserApiKey ? "TEST_USER_API_KEY" : null,
      !apiUrl ? "PLAYWRIGHT_API_URL" : null,
    ]
      .filter(Boolean)
      .join(", ");

    throw new Error(
      [
        `Unable to fetch the E2E session token for ${playwrightEnv.targetEnv || "unknown"}.`,
        `Missing required values: ${missingConfig || "none"}.`,
        "For staging in CI, set STAGING_API_URL and STAGING_TEST_USER_API_KEY before the Playwright run begins.",
        `Current PLAYWRIGHT_API_URL: ${apiUrl || "unset"}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
      ].join("\n"),
    );
  }

  const requestUrl = `${apiUrl}/v1/internal/api-jwt`;
  const response = await fetch(requestUrl, {
    headers: {
      "X-API-Key": testUserApiKey,
      "Content-Type": "application/json",
    },
    method: "GET",
  });

  if (!response.ok) {
    const responseBody = await response.text();
    const responseHint =
      response.status === 404
        ? "Check that the deployed API is exposing GET /v1/internal/api-jwt and that PLAYWRIGHT_API_URL points to the correct host."
        : "Check that the API key is valid for this environment.";

    throw new Error(
      [
        `Unable to fetch the E2E session token. Status: ${response.status}.`,
        `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
        `Request URL: ${requestUrl}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
        responseBody
          ? `Response body: ${responseBody}`
          : "Response body: empty.",
        responseHint,
      ].join("\n"),
    );
  }

  const json = (await response.json()) as { data: { jwt_token: string } };
  return json.data.jwt_token;
};

export async function authenticateE2eUser(
  page: Page,
  context: BrowserContext,
  isMobile: boolean,
  testUserKey: TestUserKey = "primaryOrgAdmin",
  testUserApiKeyOverride: string = playwrightEnv.testUserApiKey,
): Promise<void> {
  const maskedTestUserApiKey = testUserApiKeyOverride
    ? `${testUserApiKeyOverride.slice(0, 4)}...${testUserApiKeyOverride.slice(-4)}`
    : "empty";

  if (playwrightEnv.targetEnv === "staging") {
    if (!testUserApiKeyOverride) {
      throw new Error(
        [
          "Unable to log in to staging: the E2E API key is missing.",
          "Set STAGING_TEST_USER_API_KEY and pass it through to TEST_USER_API_KEY for the run.",
          `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
        ].join("\n"),
      );
    }

    await authenticateWithTemporaryApiKeyModal(page, isMobile);
    return;
  }

  if (!testUserApiKeyOverride || !apiUrl) {
    const missingConfig = [
      !testUserApiKeyOverride ? "TEST_USER_API_KEY" : null,
      !apiUrl ? "PLAYWRIGHT_API_URL" : null,
    ]
      .filter(Boolean)
      .join(", ");

    throw new Error(
      [
        `Unable to create the local E2E session for ${playwrightEnv.targetEnv || "unknown"}.`,
        `Missing required values: ${missingConfig || "none"}.`,
        `Current PLAYWRIGHT_API_URL: ${apiUrl || "unset"}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
      ].join("\n"),
    );
  }

  const userId = getTestUserId(testUserKey);
  void userId;
  const token = await fetchE2eSessionToken(testUserApiKeyOverride);
  await createSpoofedSessionCookie(context, token);

  const preNavWait = isMobile ? 2000 : 1000;
  const postNavWait = isMobile ? 4000 : 2000;
  await page.waitForTimeout(preNavWait);
  await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(postNavWait);
}

export { isTemporaryApiKeyModalFlow };

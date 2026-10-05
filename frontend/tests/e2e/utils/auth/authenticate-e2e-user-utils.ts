/**
 * authenticateE2eUser is a high-level helper for E2E test authentication.
 *
 * This helper supports two auth paths:
 * - local: bypass normal app login by fetching a server JWT from
 *   /v1/internal/api-jwt and encoding it into a spoofed client session cookie.
 * - staging: navigate to the deployed frontend, click Sign in, and submit the
 *   test user's API key in the staging API-key login modal.
 *
 * Test users are chosen via a TestUserKey (see test-users.ts). Spoofing is the
 * only supported path — seeded test users have no login credentials or MFA — so
 * any failure throws and fails the test rather than falling back to a real login.
 */

import { type BrowserContext, type Page } from "@playwright/test";
import playwrightEnv from "tests/e2e/playwright-env";
import { createSpoofedSessionCookie } from "tests/e2e/utils/auth/login-utils";
import { authenticateWithTemporaryApiKeyModal } from "tests/e2e/utils/auth/temporary-api-key-modal-auth-utils";
import {
  getTestUserId,
  type TestUserKey,
} from "tests/e2e/utils/auth/test-users";

const { baseUrl, apiUrl } = playwrightEnv;

// Fetches a JWT for a test user by calling the internal API-key JWT endpoint.
// This direct spoof-login path is used by local runs.
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
        `Unable to fetch E2E session token: missing auth configuration for ${playwrightEnv.targetEnv || "unknown"} environment.`,
        `Missing required variables: ${missingConfig || "none"}.`,
        "For staging in CI, set STAGING_API_URL and STAGING_TEST_USER_API_KEY in workflow secrets/env.",
        "CI mapping must pass STAGING_API_URL -> PLAYWRIGHT_API_URL and STAGING_TEST_USER_API_KEY -> TEST_USER_API_KEY before running Playwright.",
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

  const errorTimestamp = new Date().toISOString();

  if (!response.ok) {
    const responseBody = await response.text();
    const statusSpecificHint =
      response.status === 404
        ? "Backend : verify the staging deployment exposes GET /v1/internal/api-jwt and that PLAYWRIGHT_API_URL points at the correct deployed API."
        : "Backend : verify the API key is valid and active for /v1/internal/api-jwt in this environment.";

    throw new Error(
      [
        `unable to fetch e2e user token: response.status ${response.status}.`,
        `Timestamp: ${errorTimestamp}.`,
        `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
        `Request URL: ${requestUrl}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
        responseBody
          ? `Response body: ${responseBody}`
          : "Response body: empty.",
        statusSpecificHint,
      ].join("\n"),
    );
  }

  const json = (await response.json()) as { data: { jwt_token: string } };
  return json.data.jwt_token;
};

// Legacy e2e-token flow retained only as a rollback reference.
// const response = await fetch(`${apiUrl}/v1/internal/e2e-token`, {
//   headers: {
//     "X-API-Key": testUserManagerApiKey,
//     "Content-Type": "application/json",
//   },
//   method: "POST",
//   body: JSON.stringify({ user_id: userId }),
// });

export async function authenticateE2eUser(
  page: Page,
  context: BrowserContext,
  isMobile: boolean,
  testUserKey: TestUserKey = "primaryOrgAdmin",
  // Pass through explicitly so both local spoof-login and staging UI
  // API-key modal login do not rely on hidden/global env lookups at the
  // request boundary.
  testUserApiKeyOverride: string = playwrightEnv.testUserApiKey,
): Promise<void> {
  const maskedTestUserApiKey = testUserApiKeyOverride
    ? `${testUserApiKeyOverride.slice(0, 4)}...${testUserApiKeyOverride.slice(-4)}`
    : "empty";
  const errorTimestamp = new Date().toISOString();

  if (playwrightEnv.targetEnv === "staging") {
    // Staging uses the UI API-key modal flow instead of GET /v1/internal/api-jwt.
    if (!testUserApiKeyOverride) {
      throw new Error(
        [
          "Unable to run staging UI API-key login: TEST_USER_API_KEY is not set.",
          "For CI, set STAGING_TEST_USER_API_KEY and map it to TEST_USER_API_KEY.",
          `Timestamp: ${errorTimestamp}.`,
          `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
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
        `Unable to spoof login: missing E2E auth config for ${playwrightEnv.targetEnv || "unknown"} environment.`,
        `Missing required variables: ${missingConfig || "none"}.`,
        "For staging in CI, set STAGING_API_URL and STAGING_TEST_USER_API_KEY in workflow secrets/env.",
        "CI mapping must pass STAGING_API_URL -> PLAYWRIGHT_API_URL and STAGING_TEST_USER_API_KEY -> TEST_USER_API_KEY before the direct /v1/internal/api-jwt flow can run.",
        `Timestamp: ${errorTimestamp}.`,
        `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
        `Current PLAYWRIGHT_API_URL: ${apiUrl || "unset"}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
      ].join("\n"),
    );
  }

  const userId = getTestUserId(testUserKey);
  void userId;
  const token = await fetchE2eSessionToken(testUserApiKeyOverride);
  await createSpoofedSessionCookie(context, token);

  // Let the spoofed session cookie settle before navigating. Mobile keeps a
  // longer delay because smaller viewports hydrate more slowly.
  const preNavWait = isMobile ? 2000 : 1000;
  const postNavWait = isMobile ? 4000 : 2000;
  await page.waitForTimeout(preNavWait);
  await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(postNavWait);
}

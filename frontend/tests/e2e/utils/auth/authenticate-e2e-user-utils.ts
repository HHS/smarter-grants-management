/**
 * authenticateE2eUser is a high-level helper for E2E test authentication.
 *
 * This flow temporarily bypasses the normal app login by creating a client-side
 * spoofed session. In SGM, the direct workaround is to fetch a JWT using a test
 * user's API key at /v1/internal/api-jwt and then encode that JWT into the
 * session cookie we expect the app to read.
 *
 * Test users are chosen via a TestUserKey (see test-users.ts). Spoofing is the
 * only supported path — seeded test users have no login credentials or MFA — so
 * any failure throws and fails the test rather than falling back to a real login.
 */

import { type BrowserContext, type Page } from "@playwright/test";
import playwrightEnv from "tests/e2e/playwright-env";
import { createSpoofedSessionCookie } from "tests/e2e/utils/auth/login-utils";
import {
  getTestUserId,
  type TestUserKey,
} from "tests/e2e/utils/auth/test-users";

const { baseUrl, apiUrl } = playwrightEnv;

// Fetches a JWT for a test user by calling the internal API-key JWT endpoint.
// NOTE: This is intentionally using the direct user API key flow rather than the
// legacy managed-user e2e-token endpoint. The old request is left below as a
// commented fallback only.
export const fetchE2eSessionToken = async (
  testUserApiKey: string,
): Promise<string> => {
  if (!testUserApiKey) {
    throw new Error("Unable to spoof login: test user API key is not set");
  }

  const response = await fetch(`${apiUrl}/v1/internal/api-jwt`, {
    headers: {
      "X-API-Key": testUserApiKey,
      "Content-Type": "application/json",
    },
    method: "GET",
  });

  const maskedTestUserApiKey = testUserApiKey
    ? `${testUserApiKey.slice(0, 4)}...${testUserApiKey.slice(-4)}`
    : "empty";
  const errorTimestamp = new Date().toISOString();

  if (!response.ok) {
    throw new Error(
      [
        `unable to fetch e2e user token: response.status ${response.status}.`,
        `Timestamp: ${errorTimestamp}.`,
        `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
        "Backend engineer: verify the API key is valid and active for /v1/internal/api-jwt in this environment.",
        "Frontend engineer: verify the Playwright request is sending TEST_USER_API_KEY in the X-API-Key header.",
        "Infra engineer: verify the CI secret or environment variable is populated for this run.",
      ].join("\n"),
    );
  }

  const json = (await response.json()) as { data: { jwt_token: string } };
  return json.data.jwt_token;
};

// Legacy flow retained for rollback reference:
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
  // The direct test-user API key is intentionally passed through explicitly so
  // the E2E spoof-login flow does not rely on a hidden/global env lookup at the
  // request boundary.
  testUserApiKeyOverride: string = playwrightEnv.testUserApiKey,
): Promise<void> {
  const maskedTestUserApiKey = testUserApiKeyOverride
    ? `${testUserApiKeyOverride.slice(0, 4)}...${testUserApiKeyOverride.slice(-4)}`
    : "empty";
  const errorTimestamp = new Date().toISOString();

  if (!testUserApiKeyOverride) {
    throw new Error(
      [
        "Unable to spoof login: TEST_USER_API_KEY is not set for the direct /v1/internal/api-jwt E2E flow.",
        `Timestamp: ${errorTimestamp}.`,
        `Target environment: ${playwrightEnv.targetEnv || "unknown"}.`,
        `Current TEST_USER_API_KEY: ${maskedTestUserApiKey}.`,
        "Backend engineer: confirm the seeded test-user API key exists and is active in the target environment.",
        "Frontend engineer: confirm the value is passed through TEST_USER_API_KEY in the Playwright env.",
        "Infra engineer: confirm the GitHub secret or environment variable is populated for the CI job.",
      ].join("\n"),
    );
  }

  const userId = getTestUserId(testUserKey);
  void userId;
  const token = await fetchE2eSessionToken(testUserApiKeyOverride);
  await createSpoofedSessionCookie(context, token);

  // Give the spoofed session cookie a moment to settle before navigating, then
  // let the page hydrate the authenticated state after load. Mobile needs longer
  // waits due to slower rendering and session establishment on smaller viewports.
  const preNavWait = isMobile ? 2000 : 1000;
  const postNavWait = isMobile ? 4000 : 2000;
  await page.waitForTimeout(preNavWait);
  await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(postNavWait);
}

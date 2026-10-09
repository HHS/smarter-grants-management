/**
 * Reviewer conclusion:
 * This spec verifies that auth-token failures are emitted as structured,
 * triage-friendly errors (failed step + timestamp + actionable context).
 */

import { expect, test } from "@playwright/test";
import { fetchE2eSessionToken } from "tests/e2e/utils/auth/authenticate-e2e-user-utils";

const originalFetch = global.fetch;

test.afterEach(() => {
  // Reset global fetch so each test is isolated and does not leak mocks.
  global.fetch = originalFetch;
});

test("returns a structured error when API key is missing", async () => {
  await expect(fetchE2eSessionToken("")).rejects.toThrow(
    /Failed step: validate-token-fetch-prerequisites/,
  );
  await expect(fetchE2eSessionToken("")).rejects.toThrow(/Error time \(UTC\):/);
  await expect(fetchE2eSessionToken("")).rejects.toThrow(
    /Missing required values: TEST_USER_API_KEY/,
  );
});

test("returns a structured error when token request network call fails", async () => {
  // Simulate network failure before any HTTP response is received.
  global.fetch = () => Promise.reject(new Error("simulated network failure"));

  await expect(fetchE2eSessionToken("abcd1234")).rejects.toThrow(
    /Failed step: request-e2e-session-token/,
  );
  await expect(fetchE2eSessionToken("abcd1234")).rejects.toThrow(
    /Original error: simulated network failure/,
  );
});

test("returns a structured error when token payload is missing jwt_token", async () => {
  // Simulate a malformed success payload from /v1/internal/api-jwt.
  global.fetch = () =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ data: {} }),
    } as Response);

  await expect(fetchE2eSessionToken("abcd1234")).rejects.toThrow(
    /Failed step: validate-e2e-session-token-payload/,
  );
  await expect(fetchE2eSessionToken("abcd1234")).rejects.toThrow(
    /Response JSON is missing data\.jwt_token/,
  );
});

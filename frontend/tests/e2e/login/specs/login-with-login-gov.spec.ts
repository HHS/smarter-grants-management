/**
 * @feature Sign in to staging
 * @featureFile e2e/login/features/login-with-login-gov.feature
 * @scenario Staging API-key authentication
 * @note Legacy filename retained; this spec validates the current staging auth flow.
 */

import { expect, test, type BrowserContext, type Page } from "@playwright/test";
import playwrightEnv from "tests/e2e/playwright-env";
import { VALID_TAGS } from "tests/e2e/tags";
import { authenticateE2eUser } from "tests/e2e/utils/auth/authenticate-e2e-user-utils";
import { skipNonChromeOnStaging } from "tests/e2e/utils/auth/skip-non-chrome-staging-utils";

const { SMOKE, AUTH } = VALID_TAGS;

const { targetEnv, testUserApiKey } = playwrightEnv;

test.describe("Staging authentication tests", () => {
  // Skip non-Chrome browsers in staging
  test.beforeEach(({ page: _ }, testInfo) => {
    skipNonChromeOnStaging(testInfo);
  });

  // Skip test if env missing
  const envMissing = targetEnv !== "staging" || !testUserApiKey;
  test.skip(envMissing, "Staging E2E auth env not configured; skipping spec");

  // Scenario: signs in with the staging auth flow and reaches an authenticated state
  test(
    "Staging authentication reaches authenticated state",
    { tag: [SMOKE, AUTH] },
    async ({ page, context }: { page: Page; context: BrowserContext }) => {
      const isMobileProject = !!test.info().project.name.match(/[Mm]obile/);

      // Only start tracing manually on the first attempt. On retries, Playwright's
      // config (trace: "on-first-retry") has already started tracing, and calling
      // tracing.start() again throws "Tracing has been already started".
      const isFirstAttempt = test.info().retry === 0;
      if (isFirstAttempt) {
        await context.tracing.start({ screenshots: true, snapshots: true });
      }

      try {
        await authenticateE2eUser(page, context, isMobileProject);

        const authenticatedMarker = page
          .locator(
            'button[aria-controls="Account"], [data-testid="user-menu-trigger"], a:has-text("Sign out"), button:has-text("Sign out")',
          )
          .first();
        await expect(authenticatedMarker).toBeVisible({ timeout: 90000 });
      } finally {
        // Always stop tracing if we started it, whether the test passed or failed.
        // On retries tracing is managed by Playwright config so we skip this.
        if (isFirstAttempt) {
          await context.tracing
            .stop({ path: test.info().outputPath("trace.zip") })
            .catch(() => undefined); // ignore if tracing was never started
        }
      }
    },
  );
});

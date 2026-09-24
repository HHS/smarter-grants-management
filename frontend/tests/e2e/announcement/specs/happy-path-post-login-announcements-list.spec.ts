/**
 * @feature Opportunity - Happy Path
 * @featureFile e2e/announcement/features/happy-path-opportunities-list.feature
 * @scenario Grantor lands on announcements list page after login
 */

import {
  expect,
  test,
  type BrowserContext,
  type Page,
  type TestInfo,
} from "@playwright/test";
import {
  ANNOUNCEMENTS_LIST_PAGE_DEFINITIONS,
  getAnnouncementListPageLocator,
} from "tests/e2e/announcement/fixtures/announcement-list-definition";
import playwrightEnv from "tests/e2e/playwright-env";
import { VALID_TAGS } from "tests/e2e/tags";
import { authenticateE2eUser } from "tests/e2e/utils/auth/authenticate-e2e-user-utils";

const { GRANTOR, OPPORTUNITY_MANAGEMENT, CORE_REGRESSION } = VALID_TAGS;
const { targetEnv } = playwrightEnv;

test.describe("Grantor announcements list post-login happy path", () => {
  test.beforeEach(({ page: _ }, testInfo) => {
    if (targetEnv !== "local") {
      test.skip(
        testInfo.project.name !== "Chrome",
        "Staging MFA login is limited to Chrome to avoid OTP rate-limiting",
      );
    }
  });

  test(
    "Navigates to announcements list page after login and hides Sign in",
    { tag: [GRANTOR, OPPORTUNITY_MANAGEMENT, CORE_REGRESSION] },
    async (
      { page, context }: { page: Page; context: BrowserContext },
      testInfo: TestInfo,
    ) => {
      test.setTimeout(300_000);

      // Given I am logged in as a grantor user.
      await authenticateE2eUser(
        page,
        context,
        !!testInfo.project.name.match(/[Mm]obile/),
        "primaryOrgAdmin",
        // Temporary use of testUserApiKey for authentication
        playwrightEnv.testUserApiKey,
      );

      // Then I should not see the "Sign in" link.
      await expect(
        page.getByRole("link", { name: "Sign in", exact: true }),
      ).not.toBeVisible();

      // When I navigate to the announcements list page.
      await page.goto("/announcements");

      // Then I should be redirected to the announcements list page.
      await expect(page).toHaveURL(/\/announcements/);

      // And I should see the Announcements List heading.
      await expect(
        getAnnouncementListPageLocator(
          page,
          ANNOUNCEMENTS_LIST_PAGE_DEFINITIONS.pageHeading,
        ),
      ).toBeVisible();
    },
  );
});

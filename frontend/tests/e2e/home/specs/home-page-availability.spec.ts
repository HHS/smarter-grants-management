/**
 * @feature Home Page Availability
 * @featureFile e2e/home/features/home-page-availability.feature
 * @scenario Home page loads without signing in
 */

import { expect, test } from "@playwright/test";
import { VALID_TAGS } from "tests/e2e/tags";

const { STATIC, SMOKE } = VALID_TAGS;

test.describe("Home Page Availability", () => {
  // Scenario: Home page loads without signing in
  test(
    "home page loads without signing in",
    { tag: [STATIC, SMOKE] },
    async ({ page }) => {
      // Given I am not signed in (each test starts with a fresh browser context)
      // When I navigate to the home page
      const response = await page.goto("/", { waitUntil: "domcontentloaded" });

      // Then the page responds successfully
      expect(response?.ok()).toBeTruthy();

      // And I should see the "Welcome to Smarter Grants Management" heading
      await expect(
        page.getByRole("heading", {
          name: "Welcome to Smarter Grants Management",
        }),
      ).toBeVisible();
    },
  );
});

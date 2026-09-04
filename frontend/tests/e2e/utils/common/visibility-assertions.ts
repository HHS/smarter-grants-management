/**
 * Provides reusable visibility assertions for locators, text, and page details.
 * Usage: import { assertTextVisible, assertTextsVisibleOnPage, assertPageHeadingAndTextsVisible } from "tests/e2e/utils/common/visibility-assertions";
 */

import { expect, Locator, type Page } from "@playwright/test";

const DEFAULT_WAIT_TIMEOUT = 5000;

/** Asserts that a single visible text value exists on the page. */
export const assertTextVisible = async (page: Page, text: string) => {
  await expect(page.getByText(text).first()).toBeVisible();
};

/** Asserts visibility for a list of text values. */
export const assertTextsVisibleOnPage = async (page: Page, texts: string[]) => {
  for (const text of texts) {
    await assertTextVisible(page, text);
  }
};

/** Asserts page heading and supporting text values in one call. */
export const assertPageHeadingAndTextsVisible = async (
  page: Page,
  options: { heading: string; texts: string[] },
) => {
  await expect(
    page.getByRole("heading", { name: options.heading }),
  ).toBeVisible();

  await assertTextsVisibleOnPage(page, options.texts);
};

export const assertPageDetailsVisible = assertPageHeadingAndTextsVisible;

/** Waits for a locator to be visible and clicks it. */
export async function waitForVisibleAndClick(locator: Locator): Promise<void> {
  await locator.waitFor({ state: "visible", timeout: DEFAULT_WAIT_TIMEOUT });
  await locator.click();
}

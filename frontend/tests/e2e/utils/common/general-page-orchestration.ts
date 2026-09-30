/**
 * Shared page orchestration helpers that open a page, fill fields, and save when needed.
 * Keep navigation and save flow here so field dispatch remains reusable elsewhere.
 * Usage: import { fillFormPartial, fillForm } from "tests/e2e/utils/common/general-page-orchestration";
 */

import { type Page, type TestInfo } from "@playwright/test";
import { fillField } from "tests/e2e/utils/common/shared-field-filling";
import {
  shouldFillField,
  type FillFormConfig,
  type FormFillFieldDefinitions,
} from "tests/e2e/utils/common/types";
import {
  buildFlexibleFormNameRegex,
  openForm,
} from "tests/e2e/utils/forms/form-navigation-utils";
import { clickSaveButton } from "tests/e2e/utils/forms/save-form-utils";

/**
 * Fills a subset of fields on the current page without navigating or saving.
 * Use when the page is already open and only some fields should be filled.
 * Does NOT perform assertions - those are done in the test.
 */
export async function fillFormPartial(
  testInfo: TestInfo,
  page: Page,
  fieldDefinitions: FormFillFieldDefinitions,
  data: Record<string, string | boolean>,
): Promise<void> {
  for (const key of Object.keys(data)) {
    const fieldDef = fieldDefinitions[key as keyof FormFillFieldDefinitions];
    if (!fieldDef) {
      await testInfo.attach(`fillFormPartial-${key}-unknown-key`, {
        body: `Skipped ${key}: no matching field definition found`,
        contentType: "text/plain",
      });
      continue;
    }

    // Delegate to the shared field executor so field-type handling stays centralized in common.
    await fillField(page, fieldDef, data[key]);
  }
}

/**
 * Opens and fills a page flow from the application page, then saves it.
 * Delegates navigation to `openForm`, which owns all navigation reliability:
 * table-scoped row lookup, scroll-to-reveal, testId/href/button/global
 * fallback selectors, trial-click check, force-click retry, direct href
 * goto last resort, and URL pattern + load-state verification.
 *
 * Does NOT perform assertions - those are done in the test.
 * Assumes the current page is already an application page where the table is reachable.
 */
export async function fillForm(
  testInfo: TestInfo,
  page: Page,
  config: FillFormConfig,
  data: Record<string, string | boolean>,
  returnToApplication = true,
): Promise<void> {
  const { formName, fields, saveButtonTestId } = config;
  const applicationURL = page.url();
  await testInfo.attach("fillForm-applicationURL", {
    body: `Application URL: ${applicationURL}`,
    contentType: "text/plain",
  });
  // Derive a regex matcher for openForm. For plain strings (e.g. "SF-424 (Form)"),
  // use buildFlexibleFormNameRegex so special chars like () are properly escaped
  // and hyphens/spaces become flexible. For RegExp formNames, pass through directly.
  const formMatcher =
    formName instanceof RegExp
      ? formName
      : buildFlexibleFormNameRegex(formName);
  try {
    // Keep navigation here; the shared helper only owns field dispatch.
    // Navigation:
    // Delegate to openForm, which owns all navigation reliability:
    // table-scoped row lookup, scroll-to-reveal, testId/href/button/global
    // fallback selectors, trial-click check, force-click retry, direct href
    // goto last resort, and URL pattern + load-state verification.
    const opened = await openForm(page, formMatcher);
    if (!opened) {
      throw new Error(`Could not find or open form: ${formMatcher}`);
    }
    // Form ready check:
    // Confirm the form heading is visible before filling any fields.
    // Use buildFlexibleFormNameRegex for plain strings so special chars (parens,
    // hyphens) are properly escaped rather than treated as regex syntax.
    const formReadyMatcher =
      formName instanceof RegExp
        ? formName
        : buildFlexibleFormNameRegex(formName);
    try {
      await page
        .getByText(formReadyMatcher)
        .first()
        .waitFor({ state: "visible", timeout: 35000 });
    } catch (error) {
      throw new Error(
        `Could not find or open form heading: ${formReadyMatcher}`,
        { cause: error },
      );
    }
    for (const [fieldIdentifier, fieldConfig] of Object.entries(fields)) {
      // Fill fields only after the page has been opened and verified.
      const dataForField = data[fieldIdentifier];
      if (dataForField === undefined) {
        continue;
      }
      if (!shouldFillField(fieldConfig, data)) {
        await testInfo.attach(`fillField-${fieldIdentifier}-skipped`, {
          body: `Skipped ${fieldIdentifier}: dependency ${fieldConfig.dependsOn?.field} did not match ${fieldConfig.dependsOn?.value}`,
          contentType: "text/plain",
        });
        continue;
      }
      // Field routing is centralized in common so this loop only coordinates orchestration.
      await fillField(page, fieldConfig, dataForField);
    }

    // Run page-specific pre-save hook if defined.
    if (config.beforeSave) {
      await config.beforeSave(page);
    }
    await clickSaveButton(page, saveButtonTestId);
    if (returnToApplication) {
      await page.goto(applicationURL);
    }
  } catch (error) {
    await testInfo.attach("fillForm-error", {
      body: error instanceof Error ? error.message : String(error),
      contentType: "text/plain",
    });
    throw error;
  }
}

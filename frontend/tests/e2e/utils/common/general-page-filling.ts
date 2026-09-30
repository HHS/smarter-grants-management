/**
 * Shared page-field filling helpers that batch page fields through the common field executor.
 * Keep page-field dispatch here so page orchestration files do not need to know
 * how a specific field type is resolved.
 * Usage: import { fillPageField, fillPageFields } from "tests/e2e/utils/common/general-page-filling";
 */

import { type Page } from "@playwright/test";
import { runFieldFillBatch } from "tests/e2e/utils/common/field-batch-filling";
import { fillField } from "tests/e2e/utils/common/shared-field-filling";
import {
  type FillFieldDefinition,
  type FillPageFieldsOptions,
} from "tests/e2e/utils/common/types";

export type PageFillField = FillFieldDefinition & {
  value: string | boolean;
};

/** Fills a single page field using page-level context labels. */
export async function fillPageField(
  page: Page,
  field: PageFillField,
  data: string | boolean | undefined,
): Promise<void> {
  // Keep page-specific context in errors without duplicating field handling logic.
  await fillField(page, field, data, {
    fieldContextLabel: "page field",
  });
}

/**
 * Fills all provided page fields on the current page.
 * Does NOT perform navigation, save, or assertions.
 */
export async function fillPageFields(
  page: Page,
  fields: PageFillField[],
  options?: FillPageFieldsOptions,
): Promise<void> {
  const continueOnError = options?.continueOnError ?? false;
  // Keep batching local so callers can choose whether page-level errors stop early.
  await runFieldFillBatch({
    items: fields,
    continueOnError,
    fillItem: async (field) => {
      await fillPageField(page, field, field.value);
    },
    formatError: (field, error) => {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      return `${field.label} [${field.type}]: ${errorMessage}`;
    },
    failureSummary: (failureCount, failures) => {
      return `Failed to fill ${failureCount} field(s):\n${failures.join("\n")}`;
    },
  });
}
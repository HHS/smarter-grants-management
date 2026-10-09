/**
 * Shared helper for single-field fill execution with consistent error wrapping.
 * Keep field dispatch here so page orchestration code can stay thin and reusable.
 * Usage: import { runSharedFieldFill } from "tests/e2e/utils/common/shared-field-filling";
 */

import { type Page } from "@playwright/test";
import { fieldHandlerMap } from "tests/e2e/utils/common/field-handler-dispatcher";
import { buildFieldIdentifier } from "tests/e2e/utils/common/field-identifier";
import { type FillFieldDefinition } from "tests/e2e/utils/common/types";

type FillFieldOptions = {
  fieldContextLabel?: string;
};

type SharedFillOptions = {
  page: Page;
  field: FillFieldDefinition;
  data: string | boolean | undefined;
  fieldIdentifier?: string;
  fieldContextLabel?: string;
};

const defaultFieldContextLabel = "field";

const buildFieldContext = (
  fieldContextLabel: string,
  fieldIdentifier: string,
  field: FillFieldDefinition,
  pageUrl: string,
): string =>
  `${fieldContextLabel} '${fieldIdentifier}' (${field.type}) on ${pageUrl}`;

/** Fills one field using the shared field-fill execution path. */
export async function fillField(
  page: Page,
  field: FillFieldDefinition,
  data: string | boolean | undefined,
  options?: FillFieldOptions,
): Promise<void> {
  // Small wrapper so callers can set a context label without knowing the handler map.
  await runSharedFieldFill({
    page,
    field,
    data,
    fieldContextLabel: options?.fieldContextLabel,
  });
}

/** Fills a single field through the shared handler map with consistent error wrapping. */
export async function runSharedFieldFill(
  options: SharedFillOptions,
): Promise<void> {
  const { page, field, data } = options;
  const pageUrl = page.url();

  // Keep a stable field identifier in wrapped errors so callers get useful context.
  const fieldIdentifier =
    options.fieldIdentifier ?? buildFieldIdentifier(field);
  const fieldContextLabel =
    options.fieldContextLabel ?? defaultFieldContextLabel;
  const fieldContext = buildFieldContext(
    fieldContextLabel,
    fieldIdentifier,
    field,
    pageUrl,
  );
  const notFoundHandlerMessage = `No handler found for ${fieldContext} type: ${field.type}`;
  const wrappedErrorPrefix = `Failed to fill ${fieldContext}`;

  try {
    if (data === undefined) {
      return;
    }

    // Route through the shared field-type handler map instead of duplicating routing in wrappers.
    const handler = fieldHandlerMap[field.type];
    if (!handler) {
      throw new Error(notFoundHandlerMessage);
    }

    await handler(page, field, data);
  } catch (error) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : "Unknown error while filling field";

    // Preserve Playwright timeout/page lifecycle errors so callers can handle them upstream.
    if (
      page.isClosed() ||
      /Test timeout|Target page, context or browser has been closed/i.test(
        errorMessage,
      )
    ) {
      throw error instanceof Error ? error : new Error(errorMessage);
    }

    const wrappedError = new Error(wrappedErrorPrefix + ": " + errorMessage);
    (wrappedError as Error & { cause?: unknown }).cause = error;
    throw wrappedError;
  }
}

/**
 * Shared re-export surface for common E2E helper modules.
 * This file is the neutral import boundary for reusable page utilities.
 * Keep higher-level page flow code importing from here instead of reaching
 * into lower-level helper folders directly.
 *
 * Import pattern:
 * import { ... } from "tests/e2e/utils/common";
 *
 * Sections in this file:
 * - Field interaction helpers.
 * - Assertion helpers.
 * - Generic shared helpers.
 * - Metadata-driven page utilities.
 * - Metadata-driven validation helpers.
 */
import { formatNumberWithCommas } from "./number-formatters";

// Field interaction helpers.
export { selectOptionByLabel } from "./select-field";
export { fillDateByLabel } from "./date-field";

// Assertion helpers.
export { assertButtonEnabledDisabledStates } from "./button-state-assertions";
export { assertActionsColumnLinksByStatus } from "./actions-column-assertions";
export {
  assertPageHeadingAndTextsVisible,
  assertPageDetailsVisible,
  assertTextVisible,
  assertTextsVisibleOnPage,
} from "./visibility-assertions";

// Generic shared helpers used across page flows and fixtures.
export { formatNumberWithCommas };
export {
  createAuthenticatedPageLifecycle,
  createAuthenticatedStorageState,
  createPageWithStorageState,
  type AuthenticatedStorageState,
} from "./auth-storage-state-utils";
// Single-field fill execution stays in common so page-flow helpers stay layer-neutral.
export { fillField } from "./shared-field-filling";
export { runSharedFieldFill } from "./shared-field-filling";
export { runFieldFillBatch } from "./field-batch-filling";
export { buildPageFieldsFromDefinitions } from "./build-page-fields-from-definitions";
export { fillPageField, fillPageFields } from "./general-page-filling";
export { fillFormPartial, fillForm } from "./general-page-orchestration";

// Metadata-driven page utilities for reset/clear and duplicate-data assertions.
export {
  buildEmptyFillDataFromDefinitions,
  clearPageFieldsFromDefinitions,
} from "./clear-fields-utils";
export {
  assertDuplicateValidationMessages,
  buildDuplicateDataRegex,
  buildDuplicateDataRegexForField,
  buildDuplicateDataRegexesForDefinitions,
  buildDuplicateDataRegexFromDefinitions,
} from "./duplicate-data-validation-utils";

// Metadata-driven validation helpers and required-field gating helpers.
export {
  assertCharacterLimitMessageCount,
  assertCharacterLimitValidationsFromDefinitions,
  buildOverLimitFillData,
  getCharacterLimitValidationMessage,
  getCharacterLimitedFields,
} from "./character-limit-validation-utils";
export {
  assertRequiredFieldValidationsFromDefinitions,
  buildRequiredFieldErrorsFromDefinitions,
  getRequiredValidationFields,
} from "./required-field-validation-utils";
export { getRequiredFields } from "./required-fields-button-state-utils";
export { fillRequiredFieldsAndAssertButtonState } from "./required-fields-button-state-utils";

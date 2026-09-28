"use server";

import { ApiRequestError, parseErrorStatus } from "src/errors";
import {
  createApplicationPackage,
  saveCompetitionInstructions,
  updateApplicationPackage,
  updateApplicationPackageForms,
} from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import { FrontendErrorDetails } from "src/types/apiResponseTypes";
import {
  ApplicantTypes,
  ApplicationPackageFormsSubmitApi,
  ApplicationPackageSaveRequest,
} from "src/types/applicationPackageResponseTypes";
import { dateToTimestampOrNull } from "src/utils/dateUtil";

import { getTranslations } from "next-intl/server";
import { redirect } from "next/navigation";

export type ApplicationPackageActionState = {
  errorMessage?: string;
  successMessage?: string;
  validationErrors?: string[];
  newApplicationPackageId?: string;
};

// Make sure to return null in cases of empty string
function getFieldValue(formData: FormData, fieldName: string) {
  const value = formData.get(fieldName) as string | null;
  return value !== null && value.length == 0 ? null : value;
}

function buildRequestBody(formData: FormData) {
  // Process Who can apply
  const openToApplicants: ApplicantTypes[] = [];
  const whoCanApply = formData.get("open_to_applicants") as string;
  switch (whoCanApply) {
    case "organizations_only":
      openToApplicants.push("organization");
      break;
    case "individuals_only":
      openToApplicants.push("individual");
      break;
    case "both": {
      openToApplicants.push("organization");
      openToApplicants.push("individual");
      break;
    }
    default:
      break;
  }
  // Concatinate Contact info
  const contactFields = [
    "contact_name",
    "contact_title",
    "contact_email",
    "contact_phone",
  ];
  const contactInfo = contactFields
    .map((field) => formData.get(field) as string)
    .filter(Boolean) // Removes null, undefined, or empty values
    .join(" | ");

  // Build the request body which should match the ApplicationPackageSaveRequest
  const requestBody: ApplicationPackageSaveRequest = {
    application_package_title: getFieldValue(
      formData,
      "application_package_title",
    ),
    opening_timestamp: dateToTimestampOrNull(
      getFieldValue(formData, "opening_timestamp"),
    ),
    closing_timestamp: dateToTimestampOrNull(
      getFieldValue(formData, "closing_timestamp"),
    ),
    grace_period: (() => {
      const gracePeriod = getFieldValue(formData, "grace_period");
      return gracePeriod === null ? null : Number(gracePeriod);
    })(),
    public_application_package_id: getFieldValue(
      formData,
      "public_application_package_id",
    ),
    contact_info: contactInfo,
    open_to_applicants: openToApplicants,
  };
  return requestBody;
}

export interface FrontendErrorCause {
  // The details area actually under the cause
  details: FrontendErrorDetails;
}

function formatValidationErrors(error: unknown) {
  const formatedErrors: string[] = [];
  if (error instanceof ApiRequestError) {
    const cause = error.cause as FrontendErrorCause;
    const details = cause.details;
    // NOTE: currently this only returning one error at a time (no list)
    const errorMessage = details.field + ": " + details.message;
    return [errorMessage];
  }
  return formatedErrors;
}

export async function saveApplicationPackage(
  formData: FormData,
  requiredForms: ApplicationPackageFormsSubmitApi,
): Promise<ApplicationPackageActionState> {
  const t = await getTranslations("OpportunityCompetition.alerts");
  const announcementId = formData.get("announcementId") as string | null;
  let applicationPackageId = formData.get("applicationPackageId") as
    string | null;
  let apiResponse;

  // This should never be the case here,
  // but we need to account for this scenario to remove compile errors.
  if (!announcementId) return { errorMessage: t("genericError") };

  const requestBody = buildRequestBody(formData);

  try {
    if (!applicationPackageId) {
      apiResponse = await createApplicationPackage(announcementId, requestBody);
      applicationPackageId = apiResponse.data.application_package_id;
    } else {
      apiResponse = await updateApplicationPackage(
        announcementId,
        applicationPackageId,
        requestBody,
      );
    }

    // If the record was successfully created or updated,
    // then save the application instructions file (attachment)
    const pendingFileId = formData.get("pending-file-id") as string | null;
    if (pendingFileId) {
      await saveCompetitionInstructions(
        announcementId,
        applicationPackageId,
        pendingFileId,
      );
    }

    if (requiredForms) {
      await updateApplicationPackageForms({
        announcementId,
        applicationPackageId,
        body: { forms: requiredForms },
      });
    }

    return {
      successMessage: t("success"),
    };
  } catch (error) {
    const status =
      error instanceof ApiRequestError ? parseErrorStatus(error) : null;
    switch (status) {
      case 401:
        return { errorMessage: t("unauthenticated") };
      case 403:
        return { errorMessage: t("forbidden") };
      case 404:
        return { errorMessage: t("notFound") };
      case 422:
        return {
          errorMessage: t("validationErrors"),
          validationErrors: formatValidationErrors(error),
        };
      default:
        return { errorMessage: t("genericError") };
    }
  }
}

export async function applicationPackageFormAction(
  submitType: string,
  requiredForms: ApplicationPackageFormsSubmitApi,
  formData: FormData,
): Promise<ApplicationPackageActionState> {
  // 1. Save the form; if there are API errors, display them
  const saveResult = await saveApplicationPackage(formData, requiredForms);
  if (saveResult.errorMessage) {
    return saveResult;
  }

  // 2. Perform workflow routing
  let routeTo = null;
  switch (submitType) {
    case "saveAndExit":
      routeTo = "../overview";
      break;
    case "saveAndGoBack":
      routeTo = "../edit";
      break;
    case "saveAndContinue":
      routeTo = "../overview";
      break;
    default:
      break;
  }
  if (!routeTo) {
    return saveResult;
  } else {
    redirect(routeTo);
  }
}

"use server";

import { ApiRequestError, parseErrorStatus } from "src/errors";
import {
  createAnnouncementAttachment,
  deleteOpportunityAttachment,
} from "src/services/fetch/fetchers/announcementAttachmentFetcher";
import {
  createAnnouncementSummary,
  updateAnnouncementSummary,
} from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import {
  AnnouncementSummaryUpdateRawData,
  EDIT_FORM_VALIDATION_FIELD_NAMES,
  EditFormFields,
} from "src/types/announcement/announcementResponseTypes";
import { dateToTimestampOrNull, getConfiguredDayJs } from "src/utils/dateUtil";
import { formDataToObject } from "src/utils/formData/formDataToJson";
import { mapApiValidationErrors } from "src/utils/validationUtils";
import { z } from "zod";

import { getTranslations } from "next-intl/server";
import { redirect } from "next/navigation";

const dayjs = getConfiguredDayJs();

export type AnnouncementEditValidationErrors = {
  [field in EditFormFields]?: string[];
};

export type OpportunityEditActionState = {
  errorMessage?: string;
  successMessage?: string;
  validationErrors?: AnnouncementEditValidationErrors;
  newAnnouncementSummaryId?: string;
};

const editOpportunityFormSchema = {
  announcement_id: { type: "string" },
  announcement_summary_id: { type: "string" },
  is_forecast: { type: "boolean" },
  announcement_title: { type: "string" },
  category: { type: "string" },
  is_cost_sharing: { type: "boolean" },
  expected_number_of_awards: { type: "number" },
  estimated_total_program_funding: { type: "number" },
  award_floor: { type: "number" },
  award_ceiling: { type: "number" },
  post_timestamp: { type: "string" },
  close_timestamp: { type: "string" },
  close_timestamp_description: { type: "string" },
  funding_instruments: { type: "string" },
  funding_categories: { type: "string" },
  applicant_types: { items: { type: "string" } }, // array
  summary_description: { type: "string" },
  additional_info_url: { type: "string" },
  additional_info_url_description: { type: "string" },
  agency_contact_description: { type: "string" },
  agency_email_address: { type: "string" },
  agency_email_address_description: { type: "string" },
  forecasted_post_timestamp: { type: "string" },
  forecasted_close_timestamp: { type: "string" },
  forecasted_close_timestamp_description: { type: "string" },
};

function readStringValue(value: FormDataEntryValue | null): string {
  return typeof value === "string" ? value : "";
}

// held_pending_file_ids / deleted_attachment_ids are both JSON-stringified string arrays
function parseIdList(value: FormDataEntryValue | null): string[] {
  if (typeof value !== "string" || !value.trim()) {
    return [];
  }
  try {
    const parsed: unknown = JSON.parse(value);
    return Array.isArray(parsed)
      ? parsed.filter((item): item is string => typeof item === "string")
      : [];
  } catch {
    return [];
  }
}

// Attachments follow their own persistence model ("nothing persists until Save"), so
// creates/deletes are only ever sent to the backend as part of a successful Save - one
// call per held/marked-for-deletion id, regardless of which of the 3 submit types fired.
// A 422 from either endpoint has no form field of its own to attach to, so it always
// surfaces as a top-level errorMessage rather than an inline validationErrors entry -
// stops at the first failure rather than silently continuing through the rest of the list.
async function processAttachmentChanges(
  announcementId: string,
  formData: FormData,
  genericMessage: string,
): Promise<Pick<OpportunityEditActionState, "errorMessage"> | undefined> {
  const heldPendingFileIds = parseIdList(formData.get("held_pending_file_ids"));
  const deletedAttachmentIds = parseIdList(
    formData.get("deleted_attachment_ids"),
  );

  for (const pendingFileId of heldPendingFileIds) {
    const response = await createAnnouncementAttachment(
      announcementId,
      pendingFileId,
    );
    if (response.status_code === 422) {
      console.error("API side validation errors:", response.errors);
      const { errorMessage } = mapApiValidationErrors(
        response,
        genericMessage,
        EDIT_FORM_VALIDATION_FIELD_NAMES,
      );
      return { errorMessage: errorMessage ?? genericMessage };
    }
  }
  for (const attachmentId of deletedAttachmentIds) {
    const response = await deleteOpportunityAttachment(
      announcementId,
      attachmentId,
    );
    if (response.status_code === 422) {
      console.error("API side validation errors:", response.errors);
      const { errorMessage } = mapApiValidationErrors(
        response,
        genericMessage,
        EDIT_FORM_VALIDATION_FIELD_NAMES,
      );
      return { errorMessage: errorMessage ?? genericMessage };
    }
  }
  return undefined;
}

// These fields display comma-formatted (formatNumber() in AnnouncementEditForm.tsx) but are
// never stripped before submit, so the API's integer validation 422s on the raw comma string.
const CURRENCY_FIELD_NAMES = [
  "award_floor",
  "award_ceiling",
  "estimated_total_program_funding",
  "expected_number_of_awards",
] as const;

function stripCurrencyFormatting(formData: FormData) {
  for (const fieldName of CURRENCY_FIELD_NAMES) {
    const rawValue = formData.get(fieldName);
    if (typeof rawValue === "string") {
      formData.set(fieldName, rawValue.replace(/[$,\s]/g, ""));
    }
  }
}

// Shared by the outer catch and the create-path's local catch (see below) so a thrown
// error is mapped identically either way - the only difference is whether the caller
// still has a announcementSummaryId to merge back in.
function mapThrownError(
  error: unknown,
  alerts: (key: string) => string,
): Pick<OpportunityEditActionState, "errorMessage"> {
  const status =
    error instanceof ApiRequestError ? parseErrorStatus(error) : null;

  if (status === 401) {
    return { errorMessage: alerts("unauthenticated") };
  }
  if (status === 403) {
    return { errorMessage: alerts("forbidden") };
  }
  if (status === 404) {
    return { errorMessage: alerts("notFound") };
  }
  return { errorMessage: alerts("genericError") };
}

async function validateOpportunityEditForm(formData: FormData) {
  const validationErrors = await getTranslations(
    "OpportunityEdit.validationErrors",
  );
  const reviewAnnouncementEditSchema = z
    .object({
      announcement_title: z.string().trim(),
      category: z.string().trim(),
      summary_description: z
        .string()
        .trim()
        .min(1, { message: validationErrors("description") }),
      post_timestamp: z.string().trim(),
      forecasted_post_timestamp: z.string().trim(),
      close_timestamp: z.string().trim(),
      agency_email_address: z
        .string()
        .trim()
        .superRefine((value, ctx) => {
          if (value && !z.string().email().safeParse(value).success) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: validationErrors("contactEmailInvalid"),
            });
          }
        }),
      agency_email_address_description: z.string().trim(),
      funding_instruments: z
        .string()
        .trim()
        .min(1, { message: validationErrors("fundingType") }),
      funding_categories: z
        .string()
        .trim()
        .min(1, { message: validationErrors("fundingCategory") }),
      expected_number_of_awards: z.string().trim(),
      estimated_total_program_funding: z.string().trim(),
      award_ceiling: z.string().trim(),
      award_floor: z.string().trim(),
      applicant_types: z
        .array(z.string())
        .min(1, { message: validationErrors("eligibleApplicants") }),
      applicant_eligibility_description: z.string().trim(),
      additional_info_url: z.string().trim(),
      additional_info_url_description: z.string().trim(),
      agency_contact_description: z.string().trim(),
    })
    .superRefine(({ post_timestamp, close_timestamp }, ctx) => {
      if (!post_timestamp || !close_timestamp) {
        return;
      }

      const close = dayjs(close_timestamp);
      const publish = dayjs(post_timestamp);

      if (!close.isValid() || !publish.isValid() || close.isBefore(publish)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["close_timestamp"],
          message: validationErrors("closeDateOrder"),
        });
      }
    })
    .superRefine(({ post_timestamp, forecasted_post_timestamp }, ctx) => {
      if (!post_timestamp && !forecasted_post_timestamp) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["post_timestamp"],
          message: validationErrors("publishDate"),
        });
      }
    })
    .superRefine(({ post_timestamp }, ctx) => {
      if (!post_timestamp) {
        return;
      }

      const publish = dayjs(post_timestamp);
      const today = dayjs().startOf("day");

      if (publish.isValid() && publish.isBefore(today)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["post_timestamp"],
          message: validationErrors("publishDatePast"),
        });
      }
    })
    .superRefine(
      (
        { award_floor, award_ceiling, estimated_total_program_funding },
        ctx,
      ) => {
        const min = Number(award_floor.replace(/,/g, ""));
        const max = Number(award_ceiling.replace(/,/g, ""));
        const total = Number(estimated_total_program_funding.replace(/,/g, ""));
        // Award Minimum cannot exceed the Estimated Total Program Funding.
        if (
          award_floor &&
          estimated_total_program_funding &&
          !isNaN(min) &&
          !isNaN(total) &&
          min > total
        ) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["award_floor"],
            message: validationErrors("awardMinLessThanTotal"),
          });
        }
        // Award Maximum cannot exceed the Estimated Total Program Funding.
        if (
          award_ceiling &&
          estimated_total_program_funding &&
          !isNaN(max) &&
          !isNaN(total) &&
          max > total
        ) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["award_ceiling"],
            message: validationErrors("awardMaxLessThanTotal"),
          });
        }
        // Award Minimum cannot exceed Award Maximum.
        if (
          award_floor &&
          award_ceiling &&
          !isNaN(min) &&
          !isNaN(max) &&
          min > max
        ) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["award_floor"],
            message: validationErrors("awardMinLessThanMax"),
          });
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            path: ["award_ceiling"],
            message: validationErrors("awardMaxGreaterThanMin"),
          });
        }
      },
    );
  const applicantTypeKeys = Array.from(
    formData.keys().filter((key) => key.includes("applicant_types[")),
  );

  return reviewAnnouncementEditSchema.safeParse({
    announcement_title: readStringValue(formData.get("announcement_title")),
    category: readStringValue(formData.get("category")),
    summary_description: readStringValue(formData.get("summary_description")),
    post_timestamp: readStringValue(formData.get("post_timestamp")),
    close_timestamp: readStringValue(formData.get("close_timestamp")),
    forecasted_post_timestamp: readStringValue(
      formData.get("forecasted_post_timestamp"),
    ),
    forecasted_close_timestamp: readStringValue(
      formData.get("forecasted_close_timestamp"),
    ),
    agency_email_address: readStringValue(formData.get("agency_email_address")),
    agency_email_address_description: readStringValue(
      formData.get("agency_email_address_description"),
    ),
    award_floor: readStringValue(formData.get("award_floor")),
    award_ceiling: readStringValue(formData.get("award_ceiling")),
    funding_instruments: readStringValue(formData.get("funding_instruments")),
    funding_categories: readStringValue(formData.get("funding_categories")),
    expected_number_of_awards: readStringValue(
      formData.get("expected_number_of_awards"),
    ),
    estimated_total_program_funding: readStringValue(
      formData.get("estimated_total_program_funding"),
    ),
    applicant_types: applicantTypeKeys.map(
      (key) => formData.get(key) as string,
    ),
    applicant_eligibility_description: readStringValue(
      formData.get("applicant_eligibility_description"),
    ),
    additional_info_url: readStringValue(formData.get("additional_info_url")),
    additional_info_url_description: readStringValue(
      formData.get("additional_info_url_description"),
    ),
    agency_contact_description: readStringValue(
      formData.get("agency_contact_description"),
    ),
  });
}

const getTimestamps = (
  isForecast: boolean,
  rawBody: AnnouncementSummaryUpdateRawData,
) => {
  if (isForecast) {
    return {
      post_timestamp: null,
      forecasted_close_timestamp: dateToTimestampOrNull(
        rawBody.forecasted_close_timestamp,
      ),
      forecasted_post_timestamp: dateToTimestampOrNull(
        rawBody.forecasted_post_timestamp,
      ),
    };
  }
  return {
    close_timestamp: dateToTimestampOrNull(rawBody.close_timestamp),
    post_timestamp: dateToTimestampOrNull(rawBody.post_timestamp),
  };
};

export async function saveAnnouncementEditAction(
  isForecast: boolean,
  formData: FormData,
): Promise<OpportunityEditActionState> {
  const alerts = await getTranslations("OpportunityEdit.content.alerts");

  stripCurrencyFormatting(formData);

  const announcementId = readStringValue(
    formData.get("announcement_id"),
  ).trim();
  const announcementSummaryId = readStringValue(
    formData.get("announcement_summary_id"),
  ).trim();

  if (!announcementId) {
    return {
      errorMessage: alerts("missingSummaryContext"),
    };
  }

  const validatedFields = await validateOpportunityEditForm(formData);

  if (!validatedFields.success) {
    return {
      validationErrors: validatedFields.error.flatten().fieldErrors,
    };
  }

  try {
    if (!announcementSummaryId) {
      const rawBody = {
        ...formDataToObject<AnnouncementSummaryUpdateRawData>(
          formData,
          editOpportunityFormSchema,
          null,
        ),
        is_forecast: isForecast,
      };

      const body = {
        ...rawBody,
        ...getTimestamps(isForecast, rawBody),
        funding_categories: [rawBody.funding_categories],
        funding_instruments: [rawBody.funding_instruments],
      };
      const createResponse = await createAnnouncementSummary({
        announcementId,
        body: body,
      });

      if (createResponse.status_code === 422) {
        console.error("API side validation errors:", createResponse.errors);
        return mapApiValidationErrors(
          createResponse,
          alerts("genericError"),
          EDIT_FORM_VALIDATION_FIELD_NAMES,
        );
      }

      // caught locally (rather than by the outer catch below) because the summary itself
      // was already created successfully - the frontend still needs its id so a retry
      // after this error updates it instead of creating a duplicate, whether the failure
      // came back as a 422 response or was thrown (401/403/404/network/500)
      let attachmentError:
        Pick<OpportunityEditActionState, "errorMessage"> | undefined;
      try {
        attachmentError = await processAttachmentChanges(
          announcementId,
          formData,
          alerts("genericError"),
        );
      } catch (error) {
        attachmentError = mapThrownError(error, alerts);
      }
      if (attachmentError) {
        return {
          ...attachmentError,
          newAnnouncementSummaryId: createResponse.data
            .announcement_summary_id as string, // delete type coersion
        };
      }

      return {
        successMessage: alerts("success"),
        newAnnouncementSummaryId: createResponse.data
          .announcement_summary_id as string, // delete type coersion
      };
    }

    const rawBody = formDataToObject<AnnouncementSummaryUpdateRawData>(
      formData,
      editOpportunityFormSchema,
      null,
    );
    /*
      funding_instruments, funding_categories, applicant_types all need to be arrays of strings

      * funding_instruments, funding_categories are not implemented as multiselects, so they just need to be reformatted
      * applicant_types is handled via hidden inputs for collecting values
    */

    const body = {
      ...rawBody,
      ...getTimestamps(isForecast, rawBody),
      funding_categories: [rawBody.funding_categories],
      funding_instruments: [rawBody.funding_instruments],
    };

    const response = await updateAnnouncementSummary({
      announcementId,
      announcementSummaryId,
      body,
    });
    if (response.status_code === 422) {
      console.error("API side validation errors:", response.errors);
      return mapApiValidationErrors(
        response,
        alerts("genericError"),
        EDIT_FORM_VALIDATION_FIELD_NAMES,
      );
    }

    const attachmentError = await processAttachmentChanges(
      announcementId,
      formData,
      alerts("genericError"),
    );
    if (attachmentError) {
      return attachmentError;
    }

    return {
      successMessage: alerts("success"),
    };
  } catch (error) {
    return mapThrownError(error, alerts);
  }
}

export async function announcementEditFormAction(
  isForecast: boolean,
  createMode: boolean,
  announcementId: string,
  _prevState: OpportunityEditActionState,
  formData: FormData,
): Promise<OpportunityEditActionState> {
  // Save the form first - if there are validation or API errors, display them.
  const saveResult = await saveAnnouncementEditAction(isForecast, formData);
  const hasValidationErrors =
    saveResult.validationErrors &&
    Object.keys(saveResult.validationErrors).length > 0;
  if (saveResult.errorMessage || hasValidationErrors || !createMode) {
    return saveResult;
  }

  return redirect(`/announcement/${announcementId}/overview`);
}

import {
  AnnouncementDetail,
  Summary,
} from "src/types/announcement/announcementResponseTypes";

export type AnnouncementEditFormValues = {
  announcement_number: string;
  announcement_title: string;
  category: string;
  category_explanation: string;
  summary_description: string;
  funding_instruments: string;
  is_cost_sharing: boolean | null;
  post_timestamp?: string;
  forecasted_post_timestamp?: string;
  close_timestamp?: string;
  forecasted_close_timestamp?: string;
  close_timestamp_description?: string;
  forecasted_close_timestamp_description?: string;
  funding_categories: string;
  funding_category_description: string;
  expected_number_of_awards: string;
  estimated_total_program_funding: string;
  award_floor: string;
  award_ceiling: string;
  applicant_types: string[];
  applicant_eligibility_description: string;
  additional_info_url: string;
  additional_info_url_description: string;
  agency_contact_description: string;
  agency_email_address: string;
  agency_email_address_description: string;
};

const emptyString = (value: string | null | undefined) => value ?? "";

const numberToString = (value: number | null | undefined) =>
  value === null || value === undefined ? "" : String(value);

const getTimestamps = (
  isForecast: boolean,
  values?: Summary,
): Partial<AnnouncementEditFormValues> => {
  return isForecast
    ? {
        forecasted_post_timestamp: emptyString(
          values?.forecasted_post_timestamp,
        ),
        forecasted_close_timestamp: emptyString(
          values?.forecasted_close_timestamp,
        ),
        forecasted_close_timestamp_description: emptyString(
          values?.forecasted_close_timestamp_description,
        ),
      }
    : {
        post_timestamp: emptyString(values?.post_timestamp),
        close_timestamp: emptyString(values?.close_timestamp),
        close_timestamp_description: emptyString(
          values?.close_timestamp_description,
        ),
      };
};

const getDefaultAnnouncement = (isForecast: boolean) => {
  const timestamps = getTimestamps(isForecast);
  return {
    ...timestamps,
    announcement_number: "",
    announcement_title: "",
    category: "",
    category_explanation: "",
    summary_description: "",
    funding_instruments: "",
    is_cost_sharing: null,
    funding_categories: "",
    funding_category_description: "",
    expected_number_of_awards: "",
    estimated_total_program_funding: "",
    award_floor: "",
    award_ceiling: "",
    applicant_types: [],
    applicant_eligibility_description: "",
    additional_info_url: "",
    additional_info_url_description: "",
    agency_contact_description: "",
    agency_email_address: "",
    agency_email_address_description: "",
  };
};

export const buildAnnouncementEditInitialValues = (
  announcement: AnnouncementDetail | object,
  createMode = false,
  isForecast = false,
): AnnouncementEditFormValues => {
  if (createMode) {
    return getDefaultAnnouncement(isForecast);
  }

  const announcementDetail = announcement as AnnouncementDetail;
  const summary = announcementDetail.summary;

  return {
    ...getTimestamps(isForecast, summary),
    announcement_number: announcementDetail.announcement_number ?? "",
    announcement_title: emptyString(announcementDetail.announcement_title),
    category: emptyString(announcementDetail.category),
    category_explanation: emptyString(announcementDetail.category_explanation),
    summary_description: emptyString(summary?.summary_description),
    funding_instruments: summary?.funding_instruments?.[0] ?? "",
    is_cost_sharing: summary?.is_cost_sharing ?? true,
    funding_categories: summary?.funding_categories?.[0] ?? "",
    funding_category_description: emptyString(
      summary?.funding_category_description,
    ),
    expected_number_of_awards: numberToString(
      summary?.expected_number_of_awards,
    ),
    estimated_total_program_funding: numberToString(
      summary?.estimated_total_program_funding,
    ),
    award_floor: numberToString(summary?.award_floor),
    award_ceiling: numberToString(summary?.award_ceiling),
    applicant_types: summary?.applicant_types ?? [],
    applicant_eligibility_description: emptyString(
      summary?.applicant_eligibility_description,
    ),
    additional_info_url: emptyString(summary?.additional_info_url),
    additional_info_url_description: emptyString(
      summary?.additional_info_url_description,
    ),
    agency_contact_description: emptyString(
      summary?.agency_contact_description,
    ),
    agency_email_address: emptyString(summary?.agency_email_address),
    agency_email_address_description: emptyString(
      summary?.agency_email_address_description,
    ),
  };
};

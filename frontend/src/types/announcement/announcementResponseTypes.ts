import { AnnouncementAttachment } from "src/types/announcement/announcementAttachmentTypes";
import { APIResponse } from "src/types/apiResponseTypes";
import { ApplicationPackage } from "src/types/applicationPackageResponseTypes";

export type AnnouncementStatus =
  "archived" | "closed" | "posted" | "forecasted";

export interface AnnouncementAssistanceListing {
  assistance_listing_number: string;
  program_title: string;
}

export interface AnnouncementDocument {
  file_name: string;
  download_path: string;
  updated_at: string;
  file_description?: string;
}

interface MinimalSummary {
  close_date: string | null;
  is_forecast: boolean;
  post_date: string | null;
}

export interface Summary extends MinimalSummary {
  additional_info_url: string | null;
  additional_info_url_description: string | null;
  agency_code: string | null;
  agency_contact_description: string | null;
  agency_email_address: string | null;
  agency_email_address_description: string | null;
  agency_name: string | null;
  agency_phone_number: string | null;
  applicant_eligibility_description: string | null;
  applicant_types: string[] | null;
  archive_date: string | null;
  award_ceiling: number | null;
  award_floor: number | null;
  close_date_description: string | null;
  estimated_total_program_funding: number | null;
  expected_number_of_awards: number | null;
  fiscal_year: number | null;
  forecasted_award_date: string | null;
  forecasted_close_date: string | null;
  forecasted_close_date_description: string | null;
  forecasted_post_date: string | null;
  forecasted_project_start_date: string | null;
  funding_categories: string[] | null;
  funding_category_description: string | null;
  funding_instruments: string[] | null;
  is_cost_sharing: boolean | null;
  summary_description: string | null;
  updated_at: string;
  version_number: number | null;
}

export interface AnnouncementSummaryDetail extends Summary {
  opportunity_summary_id: string;
}

// note that we're using a type with a union here because of awkwardness inferring index signatures
// from interfaces in this case. See https://github.com/microsoft/TypeScript/issues/15300 for more info
type AnnouncementSummaryUpdateBase = {
  is_cost_sharing: boolean | null;
  summary_description: string | null;
  post_date: string | null;
  close_date: string | null;
  close_date_description: string | null;
  expected_number_of_awards: number | null;
  estimated_total_program_funding: number | null;
  award_floor: number | null;
  award_ceiling: number | null;
  additional_info_url: string | null;
  additional_info_url_description: string | null;
  funding_category_description: string | null;
  agency_contact_description: string | null;
  agency_email_address: string | null;
  applicant_eligibility_description: string | null;
  agency_email_address_description: string | null;
  applicant_types: string[];
};

export type AnnouncementSummaryUpdateRequest = {
  funding_categories: string[];
  funding_instruments: string[];
} & AnnouncementSummaryUpdateBase;

export type AnnouncementSummaryUpdateRawData = {
  funding_categories: string;
  funding_instruments: string;
} & AnnouncementSummaryUpdateBase;

export type AnnouncementSummaryCreateRequest =
  AnnouncementSummaryUpdateRequest & {
    is_forecast: boolean;
  };

export interface SavedToOrganization {
  organization_id: string;
  organization_name: string | null;
}

export type MinimalAnnouncement = {
  opportunity_id: string;
  announcement_id?: string;
  legacy_opportunity_id: number;
  opportunity_status: AnnouncementStatus;
  opportunity_title: string | null;
  announcement_title?: string | null;
  summary: MinimalSummary;
  saved_to_organizations?: SavedToOrganization[];
};

export interface BaseAnnouncement extends MinimalAnnouncement {
  agency_code: string | null;
  agency_name: string | null;
  category: string | null;
  category_explanation: string | null;
  created_at: string;
  opportunity_assistance_listings: AnnouncementAssistanceListing[]; // need to true up vs AnnouncementAssistanceListing
  opportunity_number: string;
  announcement_number?: string;
  summary: Summary;
  top_level_agency_name: string | null;
  updated_at: string;
  is_draft: boolean;
  is_simpler_grants_opportunity: boolean | null;
  saved_to_organizations?: SavedToOrganization[];
  submitted_application_count: number;
}

export interface AnnouncementDetail extends BaseAnnouncement {
  attachments: AnnouncementDocument[];
  application_packages: [ApplicationPackage] | null;
}

export interface AnnouncementApiResponse extends APIResponse {
  data: AnnouncementDetail;
}

export interface AnnouncementSummaryDetailApiResponse extends APIResponse {
  data: AnnouncementSummaryDetail;
}

export interface GrantorAnnouncementDetail extends Omit<
  AnnouncementDetail,
  "attachments"
> {
  is_draft: boolean;
  forecast_summary?: AnnouncementSummaryDetail;
  non_forecast_summary?: AnnouncementSummaryDetail;
  attachments?: AnnouncementAttachment[];
}

export interface GrantorAnnouncementApiResponse extends APIResponse {
  data: GrantorAnnouncementDetail;
}

export interface PossiblySavedBaseAnnouncement extends BaseAnnouncement {
  opportunitySaved?: boolean;
}

export type AnnouncementOverview = Pick<
  BaseAnnouncement,
  | "opportunity_title"
  | "opportunity_id"
  | "legacy_opportunity_id"
  | "opportunity_number"
  | "agency_name"
  | "agency_code"
  | "opportunity_assistance_listings"
  | "summary"
  | "opportunity_status"
>;

export interface AnnouncementListSummary {
  close_timestamp: string | null;
  is_forecast: boolean;
  post_timestamp: string | null;
  archive_timestamp: string | null;
  funding_instruments: string[];
}

export interface AnnouncementListItem {
  announcement_id: string;
  announcement_number: string | null;
  announcement_title: string | null;
  created_at: string;
  updated_at: string;
  summary: AnnouncementListSummary | null;
}

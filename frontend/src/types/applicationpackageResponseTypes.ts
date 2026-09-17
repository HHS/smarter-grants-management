import { APIResponse } from "./apiResponseTypes";
import { FormDetail } from "./formResponseTypes";
import {
  BaseAnnouncement,
  AnnouncementAssistanceListing,
} from "./announcement/announcementResponseTypes";

export interface ApplicationPackageInstructions {
  competition_instruction_id: string;
  created_at: string;
  download_path: string;
  file_name: string;
  updated_at: string;
}
export type ApplicationPackageForms = { form: FormDetail; is_required: boolean }[];

export type ApplicationPackageFormsSubmitApi = {
  form_id: string;
  is_required: boolean;
}[];

export type ApplicantTypes = "individual" | "organization";

// This is used for create and update
export type ApplicationPackageSaveRequest = {
  competition_title: string | null;
  opening_date: string | null;
  closing_date: string | null;
  contact_info: string | null;
  grace_period?: number | null;
  public_competition_id?: string | null;
  open_to_applicants: ApplicantTypes[];
};

export interface ApplicationPackageSaveApiResponse extends APIResponse {
  data: ApplicationPackage;
}

export type ApplicationPackage = {
  closing_date: string;
  competition_forms: ApplicationPackageForms;
  competition_id: string;
  competition_info: string;
  competition_instructions: ApplicationPackageInstructions[];
  competition_title: string;
  contact_info: string | null;
  expected_application_count: number | null;
  grace_period: number | null;
  is_open: boolean;
  open_to_applicants: ApplicantTypes[];
  opening_date: string;
  opportunity_assistance_listings: AnnouncementAssistanceListing[];
  opportunity_id: number;
  opportunity: BaseAnnouncement;
  public_competition_id?: string | null;
};

export interface ApplicationPackageInstructionsApiResponse extends APIResponse {
  data: {
    competition_instruction_id: string;
    file_name: string;
    created_at: string;
  };
}

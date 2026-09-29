import type { AnnouncementAssistanceListing } from "./announcement/announcementResponseTypes";
import { APIResponse } from "./apiResponseTypes";

export interface ApplicationPackageInstructions {
  applicationPackage_instruction_id: string;
  created_at: string;
  download_path: string;
  file_name: string;
  updated_at: string;
}
export type ApplicationPackageForms = {
  form_id: number;
  is_required: boolean;
}[];

export type ApplicationPackageFormsSubmitApi = {
  form_id: number;
  is_required: boolean;
}[];

export type ApplicantTypes = "individual" | "organization";

// This is used for create and update
export type ApplicationPackageSaveRequest = {
  application_package_title: string | null;
  opening_timestamp: string | null;
  closing_timestamp: string | null;
  contact_info: string | null;
  grace_period?: number | null;
  public_application_package_id?: string | null;
  open_to_applicants: ApplicantTypes[];
};

export interface ApplicationPackageSaveApiResponse extends APIResponse {
  data: ApplicationPackage;
}

export type ApplicationPackage = {
  announcement_assistance_listing: AnnouncementAssistanceListing | null;
  application_package_forms: ApplicationPackageForms;
  application_package_id: string;
  application_package_instructions: ApplicationPackageInstructions[];
  application_package_title: string;
  closing_timestamp: string;
  contact_info: string | null;
  grace_period: number | null;
  open_to_applicants: ApplicantTypes[];
  opening_timestamp: string;
  public_application_package_id?: string | null;
};

export interface ApplicationPackageInstructionsApiResponse extends APIResponse {
  data: {
    applicationPackage_instruction_id: string;
    file_name: string;
    created_at: string;
  };
}

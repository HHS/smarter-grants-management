export interface CreateAnnouncementRecord {
  announcement_id?: string;
  announcement_number: string;
  announcement_title: string;
  tagline: string;
  purpose_statement: string;
  category: string;
  category_explanation?: string;
  assistance_listing_number: string;
}

export type FieldValidationErrors = {
  opportunityNumber?: string[];
  opportunityTitle?: string[];
  tagline?: string[];
  purposeStatement?: string[];
  category?: string[];
  categoryExplanation?: string[];
  assistanceListingNumber?: string[];
};

export interface CreateAnnouncementResponse {
  validationErrors?: FieldValidationErrors;
  errorMessage?: string;
  data?: CreateAnnouncementRecord;
  success?: boolean;
}

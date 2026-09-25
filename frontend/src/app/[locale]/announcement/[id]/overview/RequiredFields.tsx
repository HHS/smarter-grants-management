// These objects define the required fields for each step
// of the opportunity publishing workflow.

export const summaryRequiredFields = {
  funding_instruments: true,
  funding_categories: true,
  post_timestamp: true,
  applicant_types: true,
};

export const applicationPackageRequiredFields = {
  open_to_applicants: true,
  application_package_title: true,
  // TBD: more required fields once this page is completed
};

export const baseOpportunityRequiredFields = {
  agency_code: true,
  category: true,
  opportunity_assistance_listings: true,
  opportunity_number: true,
  opportunity_title: true,
};

export const opportunityDetailsRequiredFields = {
  ...baseOpportunityRequiredFields,
  summary: summaryRequiredFields,
};

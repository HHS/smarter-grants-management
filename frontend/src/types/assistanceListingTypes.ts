export type AssistanceListing = {
  assistance_listing_id: string;
  assistance_listing_number: string;
  program_title: string;
  is_active: boolean;
  published_date: string;
};

export type AssistanceListingSearchRequestBody = {
  query: string;
  pagination: {
    page_offset: number;
    page_size: number;
  };
};

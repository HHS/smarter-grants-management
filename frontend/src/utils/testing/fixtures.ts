import { JSONSchema7 } from "json-schema";
import { UserProfile } from "src/types/authTypes";
import {
  AwardRecommendationDetails,
  AwardRecommendationListItem,
  AwardRecommendationStatus,
  AwardRecommendationSubmission,
} from "src/types/awardRecommendationTypes";
import { RelevantAgencyRecord } from "src/types/search/searchFilterTypes";
import {
  TestUser,
  UserDetail,
  UserDetailWithProfile,
  UserPrivilegesResponse,
  UserRole,
} from "src/types/userTypes";

export const mockAwardRecommendationStatus: AwardRecommendationStatus =
  "in_review";

export const fakeAgencyResponseData: RelevantAgencyRecord[] = [
  {
    agency_code: "DOCNIST",
    agency_name: "National Institute of Standards and Technology",
    top_level_agency: null,
    agency_id: 1,
  },
  {
    agency_code: "MOCKNIST",
    agency_name: "Mational Institute",
    top_level_agency: null,
    agency_id: 1,
  },
  {
    agency_code: "MOCKTRASH",
    agency_name: "Mational TRASH",
    top_level_agency: null,
    agency_id: 1,
  },
  {
    agency_code: "FAKEORG",
    agency_name: "Completely fake",
    top_level_agency: null,
    agency_id: 1,
  },
];

export const mockAwardRecommendationDetails: AwardRecommendationDetails = {
  award_recommendation_id: "63588df8-f2d1-44ed-a201-5804abba696a",
  award_recommendation_number: "AR-26-0001",
  award_recommendation_status: mockAwardRecommendationStatus,
  award_selection_method: "merit-review-other",
  selection_method_detail:
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute ...Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna",
  funding_strategy:
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute ...Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna",
  other_key_information:
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna",
  additional_info:
    "Additional contextual information about the award recommendation",
  review_workflow_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  award_recommendation_summary: {
    total_received_count: 200,
    recommended_for_funding_count: 150,
    recommended_without_funding_count: 25,
    not_recommended_count: 25,
    total_recommended_amount: 250000,
  },
  opportunity: {
    opportunity_id: "6a483cd8-9169-418a-8dfb-60fa6e6f51e5",
    opportunity_number: "OPP-2024-001",
    opportunity_title: "Test Funding Opportunity",
    summary: {
      opportunity_status: "posted",
      summary_description:
        "This is a test opportunity for award recommendations. It provides funding for innovative research and development projects.This is a test opportunity for award recommendations. It provides funding for innovative research and development projects.This is a test opportunity for award recommendations. It provides funding for innovative research and development projects.This is a test opportunity for award recommendations. It provides funding for innovative research and development projects.This is a test opportunity for award recommendations. It provides funding for innovative research and development projects.This is a test opportunity for award recommendations. It provides funding for innovative research and development projects.This is a test opportunity for award recommendations. It provides funding for innovative research and development projects.This is a test opportunity for award recommendations. It provides funding for innovative research and development projects.This is a test opportunity for award recommendations. It provides funding for innovative research and development projects.",
    },
  },
  created_at: "2026-01-01T00:00:00Z",
};

export const mockAwardRecommendationListItem: AwardRecommendationListItem = {
  award_recommendation_id:
    mockAwardRecommendationDetails.award_recommendation_id,
  award_recommendation_number:
    mockAwardRecommendationDetails.award_recommendation_number,
  award_recommendation_status:
    mockAwardRecommendationDetails.award_recommendation_status,
  opportunity: mockAwardRecommendationDetails.opportunity,
  award_recommendation_summary: {
    total_received_count:
      mockAwardRecommendationDetails.award_recommendation_summary
        ?.total_received_count ?? 0,
  },
};

export const mockAwardRecommendationListItemNoSubmissions: AwardRecommendationListItem =
  {
    ...mockAwardRecommendationListItem,
    award_recommendation_id: "no-submissions-award-rec-id",
    award_recommendation_number: "AR-26-0003",
    award_recommendation_summary: { total_received_count: 0 },
  };

export const mockDraftAwardRecommendationListItem: AwardRecommendationListItem =
  {
    ...mockAwardRecommendationListItem,
    award_recommendation_id: "draft-award-rec-id",
    award_recommendation_number: "AR-26-0002",
    award_recommendation_status: "draft",
  };

export const mockAwardRecommendationSubmissions: AwardRecommendationSubmission[] =
  [
    {
      award_recommendation_application_submission_id:
        "63588df8-f2d1-44ed-a201-5804abba696b",
      application_submission: {
        application_submission_id: "63588df8-f2d1-44ed-a201-5804abba696c",
        application_submission_number: "SUB-26-0001",
        project_title: "Test project",
        total_requested_amount: "50000.00",
        application: {
          application_id: "63588df8-f2d1-44ed-a201-5804abba696d",
          competition_id: "63588df8-f2d1-44ed-a201-5804abba696e",
          organization: {
            organization_id: "63588df8-f2d1-44ed-a201-5804abba696f",
            organization_name: "Test Org",
            uei: "UEI000001",
          },
        },
      },
      submission_detail: {
        award_recommendation_type: "recommended_for_funding",
        recommended_amount: "50000.00",
        general_comment: "",
        has_exception: false,
        exception_detail: "",
      },
    },
  ];

export const mockOpportunityDetail = {
  opportunity_id: "6a483cd8-9169-418a-8dfb-60fa6e6f51e5",
  legacy_opportunity_id: 1,
  opportunity_status: "posted" as const,
  opportunity_title: "Test Funding Opportunity",
  opportunity_number: "OPP-2024-001",
  agency_code: "ABC",
  agency_name: "Test Agency",
  top_level_agency_name: "Test Top Level Agency",
  category: "test-category",
  category_explanation: "This is a test category",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  opportunity_assistance_listings: [],
  attachments: [],
  competitions: null,
  summary: {
    summary_description: "",
    close_date: null,
    is_forecast: false,
    post_date: "2024-01-01",
    additional_info_url: null,
    additional_info_url_description: null,
    agency_code: "ABC",
    agency_contact_description: null,
    agency_email_address: null,
    agency_email_address_description: null,
    agency_name: "Test Agency",
    agency_phone_number: null,
    applicant_eligibility_description: null,
    applicant_types: null,
    archive_date: null,
    award_ceiling: null,
    award_floor: null,
    close_date_description: null,
    estimated_total_program_funding: null,
    expected_number_of_awards: null,
    fiscal_year: null,
    forecasted_award_date: null,
    forecasted_close_date: null,
    forecasted_close_date_description: null,
    forecasted_post_date: null,
    forecasted_project_start_date: null,
    funding_categories: null,
    funding_category_description: null,
    funding_instruments: null,
    is_cost_sharing: null,
    version_number: 1,
    opportunity_summary_id: "1",
    updated_at: "2024-01-01T00:00:00Z",
  },
};

export const fakeAttachments = [
  {
    created_at: "2007-11-02T15:23:09+00:00",
    download_path:
      "https://d3t9pc32v5noin.cloudfront.net/opportunities/40009/attachments/25293/YLP_Algeria_RFGP_09-28-07_EDITED.doc",
    file_description: "Announcement",
    file_name: "YLP_Algeria_RFGP_09-28-07_EDITED.doc",
    file_size_bytes: 111616,
    mime_type: "application/msword",
    updated_at: "2007-11-02T15:23:09+00:00",
  },
  {
    created_at: "2007-11-02T15:23:10+00:00",
    download_path:
      "https://d3t9pc32v5noin.cloudfront.net/opportunities/40009/attachments/25294/YLP_Algeria_POGI_09-26-07_EDITED.doc",
    file_description: "Mandatory POGI",
    file_name: "YLP_Algeria_POGI_09-26-07_EDITED.doc",
    file_size_bytes: 122880,
    mime_type: "application/msword",
    updated_at: "2007-11-02T15:23:10+00:00",
  },
];

export const fakeAgencyResponseDataWithTopLevel: RelevantAgencyRecord[] = [
  {
    agency_code: "DOC-DOCNIST",
    agency_name: "National Institute of Standards and Technology",
    top_level_agency: {
      agency_code: "DOC",
      agency_name: "Detroit Optical Company",
      agency_id: 11,
      top_level_agency: null,
    },
    agency_id: 1,
  },
  {
    agency_code: "MOCK-NIST",
    agency_name: "Mational Institute",
    top_level_agency: {
      agency_code: "MOCK",
      agency_name: "A mock",
      agency_id: 12,
      top_level_agency: null,
    },
    agency_id: 2,
  },
  {
    agency_code: "MOCKTRASH",
    agency_name: "Mational TRASH",
    top_level_agency: {
      agency_code: "MOCK",
      agency_name: "A mock",
      agency_id: 12,
      top_level_agency: null,
    },
    agency_id: 3,
  },
  {
    agency_code: "FAKEORG",
    agency_name: "Completely fake",
    top_level_agency: null,
    agency_id: 4,
  },
];

export const fakeSearchParamDict = {
  status: "forecasted,posted,archived,closed",
  eligibility: "state_governments",
  query: "simpler",
  category: "recovery_act",
  agency: "CPSC",
  fundingInstrument: "cooperative_agreement",
  andOr: "OR",
  sortby: "closeDateAsc",
};

export const fakeResponsiveTableHeaders = [
  { cellData: "hi" },
  { cellData: "a heading" },
  { cellData: "table header cell" },
];

export const fakeResponsiveTableRows = [
  [
    { cellData: "hi from row one", stackOrder: 1 },
    { cellData: "i am column two", stackOrder: 0 },
    { cellData: "some data", stackOrder: -1 },
  ],
  [
    { cellData: "hi from row two", stackOrder: 1 },
    { cellData: "still column two", stackOrder: 0 },
    { cellData: "some more data", stackOrder: -1 },
  ],
  [
    { cellData: "hi from row three", stackOrder: 1 },
    { cellData: "column two", stackOrder: 0 },
    { cellData: "even more data", stackOrder: -1 },
  ],
];

export const fakeCompetition = {
  closing_date: "1-1-30",
  competition_forms: [
    {
      form: {
        form_id: "123e4567-e89b-12d3-a456-426614174000",
        form_json_schema: {
          properties: {
            ApplicationNumber: {
              maxLength: 120,
              minLength: 1,
              title: "Application number",
              type: "number",
            },
            Date: {
              format: "date",
              title: "Date of application ",
              type: "string",
            },
            Description: {
              maxLength: 15,
              minLength: 0,
              title: "Description for application",
              type: "string",
            },
            Title: {
              maxLength: 60,
              minLength: 1,
              title: "Title",
              type: "string",
            },
          },
          title: "Test form for testing",
          type: "object",
        },
      },
      is_required: true,
    },
  ],
  competition_id: "1",
  competition_info: "info",
  competition_instructions: [
    {
      created_at: "2025-06-13T20:17:16.491Z",
      download_path:
        "https://cdn.example.com/competition-instructions/file.pdf",
      file_name: "competition_instructions.pdf",
      updated_at: "2025-06-13T20:17:16.491Z",
    },
  ],
  competition_title: "cool competition",
  contact_info: null,
  is_open: true,
  open_to_applicants: ["individual", "organization"],
  opening_date: "1-1-25",
  opportunity_assistance_listings: [
    {
      assistance_listing_number: "43.012",
      program_title: "Space Technology",
    },
  ],
  opportunity_id: "2",
};

export const fakeFieldSchema: JSONSchema7 = {
  maxLength: 15,
  minLength: 0,
  title: "Description for application",
  type: "string",
};

export const fakeUser: UserDetail = {
  user_id: "1",
  email: "not-the-real-email@fake.com",
  first_name: "joe",
  last_name: "quisling",
};

export const fakeUserWithProfile: UserDetailWithProfile = {
  user_id: "1",
  email: "not-the-real-email@fake.com",
  external_user_type: "whatever",
  profile: {
    first_name: "joe",
    last_name: "quisling",
  },
};

export const fakeUserRole: UserRole = {
  role_id: "1",
  role_name: "role_1",
  privileges: ["view_application", "manage_org_members"],
};

export const fakeUserPrivilegesResponse: UserPrivilegesResponse = {
  user_id: "1",
  organization_users: [
    {
      organization: {
        organization_id: "1",
      },
      organization_user_roles: [
        {
          role_id: "1",
          role_name: "role_1",
          privileges: ["view_application", "manage_org_members"],
        },
      ],
    },
    {
      organization: {
        organization_id: "4",
      },
      organization_user_roles: [
        {
          role_id: "4",
          role_name: "role_4",
          privileges: ["view_application", "get_submitted_applications"],
        },
      ],
    },
  ],
  application_users: [
    {
      application: {
        application_id: "1",
      },
      application_user_roles: [
        {
          role_id: "2",
          role_name: "role_2",
          privileges: ["view_application"],
        },
      ],
    },
  ],
  agency_users: [
    {
      agency: {
        agency_id: "3",
      },
      agency_user_roles: [
        {
          role_id: "3",
          role_name: "role_3",
          privileges: ["manage_agency_members"],
        },
      ],
    },
    {
      agency: {
        agency_id: "5",
      },
      agency_user_roles: [
        {
          role_id: "5",
          role_name: "role_5",
          privileges: ["manage_agency_members"],
        },
      ],
    },
  ],
};

export const fakeTestUser: TestUser = {
  first_name: "hi",
  last_name: "there",
  oauth_id: "id",
  user_api_key: "key",
  user_id: "user",
  user_jwt: "jwt",
};

export const fakeUserProfile: UserProfile = {
  token: "a token",
  user_id: "an id",
};

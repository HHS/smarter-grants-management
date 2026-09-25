import { AnnouncementDetail } from "src/types/announcement/announcementResponseTypes";

import { buildAnnouncementEditInitialValues } from "./announcementEditFormConfig";

function makeOpportunity(
  summaryOverrides: Partial<AnnouncementDetail["summary"]> = {},
  opportunityOverrides: Partial<AnnouncementDetail> = {},
): AnnouncementDetail {
  return {
    //delete opportunity params
    opportunity_id: "opp-1",
    opportunity_status: "posted",
    opportunity_title: "Test Opportunity",
    opportunity_number: "OPP-001",
    legacy_opportunity_id: 1,
    announcement_id: "opp-1",
    announcement_status: "posted",
    announcement_title: "Test Opportunity",
    announcement_number: "OPP-001",
    legacy_announcement_id: 1,
    category: "discretionary",
    category_explanation: null,
    agency_code: "TEST",
    agency_name: "Test Agency",
    top_level_agency_name: null,
    created_at: "2026-01-01",
    updated_at: "2026-01-01",
    is_draft: true,
    is_simpler_grants_opportunity: true,
    opportunity_assistance_listings: [],
    attachments: [],
    application_packages: null,
    saved_to_organizations: [],
    submitted_application_count: 0,
    summary: {
      close_timestamp: "2026-06-01",
      is_forecast: false,
      post_timestamp: "2026-05-01",
      additional_info_url: "https://example.com",
      additional_info_url_description: "More info",
      agency_code: "TEST",
      agency_contact_description: "Contact us",
      agency_email_address: "test@example.com",
      agency_email_address_description: "Email us",
      agency_name: "Test Agency",
      agency_phone_number: null,
      applicant_eligibility_description: "Open to all",
      applicant_types: ["individuals"],
      archive_date: null,
      award_ceiling: 100000,
      award_floor: 1000,
      close_timestamp_description: null,
      estimated_total_program_funding: 500000,
      expected_number_of_awards: 5,
      fiscal_year: null,
      forecasted_award_date: null,
      forecasted_close_timestamp: null,
      forecasted_close_timestamp_description: null,
      forecasted_post_timestamp: null,
      forecasted_project_start_date: null,
      funding_categories: ["education"],
      funding_category_description: null,
      funding_instruments: ["grant"],
      is_cost_sharing: true,
      summary_description: "A test description",
      updated_at: "2026-01-01",
      version_number: 1,
      ...summaryOverrides,
    },
    ...opportunityOverrides,
  };
}

describe("buildAnnouncementEditInitialValues", () => {
  it("maps opportunity and summary fields to form values", () => {
    const result = buildAnnouncementEditInitialValues(makeOpportunity());

    expect(result.announcement_title).toBe("Test Opportunity");
    expect(result.category).toBe("discretionary");
    expect(result.summary_description).toBe("A test description");
    expect(result.funding_instruments).toBe("grant");
    expect(result.funding_categories).toBe("education");
    expect(result.award_floor).toBe("1000");
    expect(result.award_ceiling).toBe("100000");
    expect(result.estimated_total_program_funding).toBe("500000");
    expect(result.expected_number_of_awards).toBe("5");
    expect(result.applicant_types).toEqual(["individuals"]);
    expect(result.is_cost_sharing).toBe(true);
    expect(result.post_timestamp).toBe("2026-05-01");
    expect(result.close_timestamp).toBe("2026-06-01");
    expect(result.agency_email_address).toBe("test@example.com");
  });

  it("returns empty string for null numeric summary fields (numberToString null branch)", () => {
    const result = buildAnnouncementEditInitialValues(
      makeOpportunity({
        award_floor: null,
        award_ceiling: null,
        estimated_total_program_funding: null,
        expected_number_of_awards: null,
      }),
    );

    expect(result.award_floor).toBe("");
    expect(result.award_ceiling).toBe("");
    expect(result.estimated_total_program_funding).toBe("");
    expect(result.expected_number_of_awards).toBe("");
  });

  it("falls back to empty string when announcement_title is null", () => {
    const result = buildAnnouncementEditInitialValues(
      makeOpportunity({}, { announcement_title: null }),
    );

    expect(result.announcement_title).toBe("");
  });

  it("returns empty string when funding_instruments array is empty", () => {
    const result = buildAnnouncementEditInitialValues(
      makeOpportunity({ funding_instruments: [] }),
    );

    expect(result.funding_instruments).toBe("");
  });

  it("returns empty string when funding_instruments is null", () => {
    const result = buildAnnouncementEditInitialValues(
      makeOpportunity({ funding_instruments: null }),
    );

    expect(result.funding_instruments).toBe("");
  });

  it("returns empty array when applicant_types is null", () => {
    const result = buildAnnouncementEditInitialValues(
      makeOpportunity({ applicant_types: null }),
    );

    expect(result.applicant_types).toEqual([]);
  });

  it("returns empty string when funding_categories is empty", () => {
    const result = buildAnnouncementEditInitialValues(
      makeOpportunity({ funding_categories: [] }),
    );

    expect(result.funding_categories).toBe("");
  });
});

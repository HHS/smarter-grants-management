import { render, screen } from "@testing-library/react";
import { axe } from "jest-axe";
import { GrantorAnnouncementDetail } from "src/types/announcement/announcementResponseTypes";

import { AnnouncementDetailsHeader } from "src/components/grantor-announcements/AnnouncementDetailsHeader";

jest.mock("next-intl", () => ({
  useTranslations: jest
    .fn()
    .mockReturnValue((key: string, params?: Record<string, string>) => {
      const translations: Record<string, string> = {
        opportunityNumber: `Announcement #: ${params?.number ?? ""}`,
        title: "Title:",
        agency: "Agency:",
        subAgency: "Sub-agency:",
        draft: "Draft",
        lastUpdated: "Last updated:",
      };
      return translations[key] ?? key;
    }),
}));

const mockOpportunityData: GrantorAnnouncementDetail = {
  opportunity_id: "abc-123",
  announcement_id: "abc-123",
  legacy_opportunity_id: 1,
  opportunity_number: "PAR-25-316",
  announcement_number: "PAR-25-316",
  opportunity_title: "Workforce Innovation Sample Grant",
  announcement_title: "Workforce Innovation Sample Grant",
  agency_name: "Workforce Innovation Sub",
  top_level_agency_name: "Workforce Innovation Agency",
  is_draft: true,
  updated_at: "2026-01-08T12:00:00Z",
  opportunity_status: "posted",
  opportunity_assistance_listings: [],
  agency_code: null,
  category: null,
  category_explanation: null,
  created_at: "2026-01-01T00:00:00Z",
  summary: {
    close_date: null,
    is_forecast: false,
    post_date: null,
  },
} as unknown as GrantorAnnouncementDetail;

describe("AnnouncementDetailsHeader", () => {
  it("should not have accessibility violations", async () => {
    const { container } = render(
      <AnnouncementDetailsHeader
        opportunityData={mockOpportunityData}
        locale="en"
      />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("renders the opportunity number in the heading", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={mockOpportunityData}
        locale="en"
      />,
    );
    expect(
      screen.getByRole("heading", { name: /PAR-25-316/ }),
    ).toBeInTheDocument();
  });

  it("renders the title", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={mockOpportunityData}
        locale="en"
      />,
    );
    expect(
      screen.getByText("Workforce Innovation Sample Grant"),
    ).toBeInTheDocument();
  });

  it("renders agency and sub-agency", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={mockOpportunityData}
        locale="en"
      />,
    );
    expect(screen.getByText(/Workforce Innovation Agency/)).toBeInTheDocument();
    expect(screen.getByText(/Workforce Innovation Sub/)).toBeInTheDocument();
  });

  it("renders the Draft badge when is_draft is true", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={mockOpportunityData}
        locale="en"
      />,
    );
    expect(screen.getByText("Draft")).toBeInTheDocument();
  });

  it("does not render the Draft badge when is_draft is false", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={{ ...mockOpportunityData, is_draft: false }}
        locale="en"
      />,
    );
    expect(screen.queryByText("Draft")).not.toBeInTheDocument();
  });

  it("renders the last updated date formatted as MM/dd/YYYY", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={mockOpportunityData}
        locale="en"
      />,
    );
    expect(screen.getByText("01/08/2026")).toBeInTheDocument();
  });

  it("formats last updated in Eastern Time near UTC midnight", () => {
    // 8:38 PM ET on 06/20/2026 is 00:38 UTC on 06/21/2026
    render(
      <AnnouncementDetailsHeader
        opportunityData={{
          ...mockOpportunityData,
          updated_at: "2026-06-21T00:38:00Z",
        }}
        locale="en"
      />,
    );
    expect(screen.getByText("06/20/2026")).toBeInTheDocument();
    expect(screen.queryByText("06/21/2026")).not.toBeInTheDocument();
  });

  it("renders -- for missing title", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={{ ...mockOpportunityData, announcement_title: null }}
        locale="en"
      />,
    );
    expect(screen.getByText("--")).toBeInTheDocument();
  });

  it("does not render sub-agency separator when agency_name is null", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={{ ...mockOpportunityData, agency_name: null }}
        locale="en"
      />,
    );
    expect(screen.queryByText("Sub-agency:")).not.toBeInTheDocument();
  });

  it("renders the back to overview link when hasBackToOverview is true", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={{ ...mockOpportunityData, agency_name: null }}
        locale="en"
        hasBackToOverview={true}
      />,
    );

    const link = screen.getByRole("link", { name: "backToOverview" });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "../abc-123/overview");
  });

  it("does not render the back to overview link when hasBackToOverview is false", () => {
    render(
      <AnnouncementDetailsHeader
        opportunityData={{ ...mockOpportunityData, agency_name: null }}
        locale="en"
        hasBackToOverview={false}
      />,
    );

    const link = screen.queryByRole("link", { name: "backToOverview" });
    expect(link).not.toBeInTheDocument();
  });
});

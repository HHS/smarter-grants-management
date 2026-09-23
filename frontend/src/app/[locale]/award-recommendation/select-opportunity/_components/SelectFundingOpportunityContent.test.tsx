import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createAwardRecommendationAction } from "src/app/[locale]/award-recommendation/select-opportunity/actions";
import { AnnouncementListItem } from "src/types/announcement/announcementResponseTypes";

import { SelectFundingOpportunityContent } from "./SelectFundingOpportunityContent";

const pushMock = jest.fn();

jest.mock(
  "src/app/[locale]/award-recommendation/select-opportunity/actions",
  () => ({
    createAwardRecommendationAction: jest.fn(),
  }),
);

jest.mock("next-intl", () => ({
  useTranslations: () => (key: string) => {
    const translations: Record<string, string> = {
      whichFundingOpportunity: "Which Funding Opportunity?",
      cancelButtonText: "Cancel",
      startButtonText: "Start",
      "columns.fundingOpportunityNumber": "Funding opportunity number",
      "columns.fundingOpportunityName": "Funding opportunity name",
      "columns.submittedApplications": "Submitted applications",
      "columns.action": "Action",
    };

    return translations[key] ?? key;
  },
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

describe("SelectFundingOpportunityContent", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockAnnouncement = (
    overrides: Partial<AnnouncementListItem> = {},
  ): AnnouncementListItem => ({
    announcement_id: "opp-1",
    announcement_number: "OPP-001",
    announcement_title: "Test Opportunity",
    created_at: "2026-06-23T00:00:00Z",
    updated_at: "2026-06-23T00:00:00Z",
    summary: {
      close_timestamp: null,
      is_forecast: false,
      post_timestamp: "2026-06-23T00:00:00Z",
      archive_timestamp: null,
      funding_instruments: [],
    },

    ...overrides,
  });

  const mockAnnouncements: AnnouncementListItem[] = [mockAnnouncement()];

  it("renders the funding opportunity heading", () => {
    render(
      <SelectFundingOpportunityContent announcements={mockAnnouncements} />,
    );

    expect(
      screen.getByRole("heading", {
        name: "Which Funding Opportunity?",
        level: 2,
      }),
    ).toBeInTheDocument();
  });

  it("renders the funding opportunities table", () => {
    render(
      <SelectFundingOpportunityContent announcements={mockAnnouncements} />,
    );

    expect(screen.getByText("OPP-001")).toBeInTheDocument();
    expect(screen.getByText("Test Opportunity")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders the cancel button", () => {
    render(
      <SelectFundingOpportunityContent announcements={mockAnnouncements} />,
    );

    expect(
      screen.getByRole("button", {
        name: "Cancel",
      }),
    ).toBeInTheDocument();
  });

  it("navigates to home when cancel is clicked", async () => {
    const user = userEvent.setup();

    render(
      <SelectFundingOpportunityContent announcements={mockAnnouncements} />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(pushMock).toHaveBeenCalledWith("/");
  });

  it("creates an award recommendation and navigates to the detail page", async () => {
    const user = userEvent.setup();

    jest.mocked(createAwardRecommendationAction).mockResolvedValue({
      awardRecommendationId: "award-rec-1",
    });

    render(
      <SelectFundingOpportunityContent announcements={mockAnnouncements} />,
    );

    await user.click(screen.getByRole("button", { name: /Start/i }));

    expect(createAwardRecommendationAction).toHaveBeenCalledWith("opp-1");
    expect(pushMock).toHaveBeenCalledWith(
      "/award-recommendation/award-rec-1/edit",
    );
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import {
  fakeForecastSummary,
  fakeSynopsisSummary,
  mockAnnouncement,
} from "src/utils/testing/fixtures";

import SummaryEditView from "./SummaryEditView";

const mockAnnouncementEditFormAction = jest.fn();
const mockClientFetch = jest.fn();
const mockGetAnnouncement = jest.fn().mockResolvedValue({
  data: {
    announcement_id: "1",
    forecast_summary: { announcement_summary_id: "2" },
  },
});

jest.mock("src/hooks/useClientFetch", () => ({
  useClientFetch: jest.fn(() => ({
    clientFetch: mockClientFetch,
  })),
}));

jest.mock(
  "src/app/[locale]/announcement/[id]/summary/[summaryId]/actions",
  () => ({
    announcementEditFormAction: () =>
      mockAnnouncementEditFormAction() as unknown,
  }),
);

jest.mock("src/services/fetch/fetchers/grantorAnnouncementFetcher", () => ({
  getAnnouncement: (arg: unknown): unknown =>
    mockGetAnnouncement(arg) as unknown,
}));

describe("SummaryEditView", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("passes accessibility scan", async () => {
    const { container } = render(
      <SummaryEditView
        announcementId="1"
        summaryId="2"
        isForecast={undefined}
      />,
    );
    const results = await waitFor(() => axe(container));

    expect(results).toHaveNoViolations();
  });
  it("renders the save buttons", async () => {
    const component = await SummaryEditView({
      announcementId: "1",
      summaryId: "2",
    });
    render(component);

    const saveButtons = screen.getAllByRole("button", { name: "Save" });
    expect(saveButtons).toHaveLength(2);
  });

  it("calls the form action when save is clicked", async () => {
    mockAnnouncementEditFormAction.mockReturnValue({});

    const component = await SummaryEditView({
      announcementId: "1",
      summaryId: "2",
    });
    render(component);

    const saveButtons = screen.getAllByRole("button", { name: "Save" });
    const saveButton = saveButtons[0];
    fireEvent.click(saveButton);

    expect(mockAnnouncementEditFormAction).toHaveBeenCalledTimes(1);
  });
  it("selects the correct summary for non-forecast", async () => {
    mockAnnouncementEditFormAction.mockReturnValue({});
    mockGetAnnouncement.mockResolvedValue({
      data: {
        ...mockAnnouncement,
        announcement_id: "1",
        non_forecast_summary: {
          ...fakeSynopsisSummary,
          announcement_summary_id: "2",
        },
      },
    });

    const component = await SummaryEditView({
      announcementId: "1",
      summaryId: "2",
      isForecast: false,
    });
    render(component);

    const title = screen.getByText("A test synopsis description");
    expect(title).toBeInTheDocument();
  });

  it("selects the correct summary for forecast", async () => {
    mockAnnouncementEditFormAction.mockReturnValue({});
    mockGetAnnouncement.mockResolvedValue({
      data: {
        ...mockAnnouncement,
        announcement_id: "1",
        forecast_summary: {
          ...fakeForecastSummary,
          announcement_summary_id: "2",
        },
      },
    });

    const component = await SummaryEditView({
      announcementId: "1",
      summaryId: "2",
      isForecast: true,
    });
    render(component);

    const title = screen.getByText("A FORECAST description");
    expect(title).toBeInTheDocument();
  });

  describe("error handling", () => {
    it("displays error if summary type not specified when creating", () => {});
    it("handles pre-emptive authentication errors when fetching announcement data", () => {});
    it("handles 404 when fetching announcement data", () => {});
    it("handles 403 when fetching announcement data", () => {});
    it("handles other errors when fetching announcement data", () => {});
    it("displays error when summary id is not suppplied in edit mode", () => {});
    it("displays error if no announcement summaries match provided summary id", () => {});
    it("displays error if announcement id in url doesnt match fetched announcement id", () => {});
    it("displays error if forecast already exists in forecast create mode", () => {});
    it("displays error if synopsis already exists in synopsis create mode", () => {});
    it("displays error if attempting to edit non-existent forecast", () => {});
    it("displays error if attempting to edit non-existent synopsis", () => {});
  });
});

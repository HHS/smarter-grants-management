import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import {
  ForbiddenError,
  InternalServerError,
  MissingAuthError,
  NotFoundError,
} from "src/errors";
import {
  fakeForecastSummary,
  fakeSynopsisSummary,
  mockAnnouncement,
} from "src/utils/testing/fixtures";

import SummaryEditView from "./SummaryEditView";

const mockAnnouncementEditFormAction = jest.fn();
const mockClientFetch = jest.fn();
const mockGetAnnouncement = jest.fn();

const mockNotFound = jest.fn();

jest.mock("next/navigation", () => ({
  notFound: (...args: unknown[]) => mockNotFound(...args) as unknown,
}));

jest.mock("src/hooks/useClientFetch", () => ({
  useClientFetch: () => mockClientFetch() as unknown,
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
  beforeEach(() => {
    mockGetAnnouncement.mockResolvedValue({
      data: {
        announcement_id: "1",
        forecast_summary: { announcement_summary_id: "2" },
      },
    });
    mockClientFetch.mockReturnValue({ clientFetch: jest.fn() });
  });
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

  it("selects the correct summary for create mode", async () => {
    mockAnnouncementEditFormAction.mockReturnValue({});
    mockGetAnnouncement.mockResolvedValue({
      data: {
        ...mockAnnouncement,
        announcement_id: "1",
      },
    });

    const component = await SummaryEditView({
      announcementId: "1",
      summaryId: "2",
      isForecast: true,
      createMode: true,
    });
    render(component);

    const forecastTitle = screen.queryByText("A FORECAST description");
    expect(forecastTitle).not.toBeInTheDocument();

    const synopsisTitle = screen.queryByText("A test synopsis description");
    expect(synopsisTitle).not.toBeInTheDocument();
  });

  describe("error handling", () => {
    it("displays error if summary type not specified when creating", async () => {
      const component = await SummaryEditView({
        announcementId: "1",
        summaryId: "2",
        createMode: true,
      });
      render(component);

      const title = screen.getByText("genericMessage");
      expect(title).toBeInTheDocument();
      const saveButton = screen.queryByRole("button", { name: "Save" });
      expect(saveButton).not.toBeInTheDocument();
    });
    it("handles pre-emptive authentication errors when fetching announcement data", async () => {
      mockGetAnnouncement.mockRejectedValue(new MissingAuthError());

      const component = await SummaryEditView({
        announcementId: "1",
        summaryId: "2",
      });
      render(component);

      const title = screen.getByText("unauthorized");
      expect(title).toBeInTheDocument();
      const saveButton = screen.queryByRole("button", { name: "Save" });
      expect(saveButton).not.toBeInTheDocument();
    });
    it("handles 404 when fetching announcement data", async () => {
      mockGetAnnouncement.mockRejectedValue(new NotFoundError("not found"));

      // the real notFound() throws to halt rendering, the mock does not
      await SummaryEditView({
        announcementId: "1",
        summaryId: "2",
      });

      expect(mockNotFound).toHaveBeenCalledTimes(1);
    });
    it("handles 403 when fetching announcement data", async () => {
      mockGetAnnouncement.mockRejectedValue(new ForbiddenError("forbidden"));

      const component = await SummaryEditView({
        announcementId: "1",
        summaryId: "2",
      });
      render(component);

      const title = screen.getByText("unauthorized");
      expect(title).toBeInTheDocument();
      const saveButton = screen.queryByRole("button", { name: "Save" });
      expect(saveButton).not.toBeInTheDocument();
    });
    it("handles other errors when fetching announcement data", async () => {
      mockGetAnnouncement.mockRejectedValue(
        new InternalServerError("server error"),
      );

      const component = await SummaryEditView({
        announcementId: "1",
        summaryId: "2",
      });
      render(component);

      const title = screen.getByText("genericMessage");
      expect(title).toBeInTheDocument();
      const saveButton = screen.queryByRole("button", { name: "Save" });
      expect(saveButton).not.toBeInTheDocument();
    });
    it("displays error when summary id is not suppplied in edit mode", async () => {
      mockGetAnnouncement.mockResolvedValue({
        data: { ...mockAnnouncement, announcement_id: "1" },
      });

      const component = await SummaryEditView({
        announcementId: "1",
      });
      render(component);

      const title = screen.getByText("genericMessage");
      expect(title).toBeInTheDocument();
      const saveButton = screen.queryByRole("button", { name: "Save" });
      expect(saveButton).not.toBeInTheDocument();
    });
    it("displays error if no announcement summaries match provided summary id", async () => {
      mockGetAnnouncement.mockResolvedValue({
        data: {
          ...mockAnnouncement,
          announcement_id: "1",
          non_forecast_summary: {
            ...fakeSynopsisSummary,
            announcement_summary_id: "3",
          },
        },
      });

      const component = await SummaryEditView({
        announcementId: "1",
        summaryId: "2",
      });
      render(component);

      const title = screen.getByText("genericMessage");
      expect(title).toBeInTheDocument();
      const saveButton = screen.queryByRole("button", { name: "Save" });
      expect(saveButton).not.toBeInTheDocument();
    });
    it("displays error if announcement id in url doesnt match fetched announcement id", async () => {
      mockGetAnnouncement.mockResolvedValue({
        data: {
          ...mockAnnouncement,
          announcement_id: "999",
          non_forecast_summary: {
            ...fakeSynopsisSummary,
            announcement_summary_id: "2",
          },
        },
      });

      const component = await SummaryEditView({
        announcementId: "1",
        summaryId: "2",
      });
      render(component);

      const title = screen.getByText("We're sorry.");
      expect(title).toBeInTheDocument();
      const saveButton = screen.queryByRole("button", { name: "Save" });
      expect(saveButton).not.toBeInTheDocument();
    });
    it("displays error if forecast already exists in forecast create mode", async () => {
      mockGetAnnouncement.mockResolvedValue({
        data: {
          ...mockAnnouncement,
          announcement_id: "1",
          forecast_summary: fakeForecastSummary,
        },
      });

      const component = await SummaryEditView({
        announcementId: "1",
        createMode: true,
        isForecast: true,
      });
      render(component);

      const title = screen.getByText("We're sorry.");
      expect(title).toBeInTheDocument();
      const saveButton = screen.queryByRole("button", { name: "Save" });
      expect(saveButton).not.toBeInTheDocument();
    });
    it("displays error if synopsis already exists in synopsis create mode", async () => {
      mockGetAnnouncement.mockResolvedValue({
        data: {
          ...mockAnnouncement,
          announcement_id: "1",
          non_forecast_summary: fakeSynopsisSummary,
        },
      });

      const component = await SummaryEditView({
        announcementId: "1",
        createMode: true,
        isForecast: false,
      });
      render(component);

      const title = screen.getByText("We're sorry.");
      expect(title).toBeInTheDocument();
      const saveButton = screen.queryByRole("button", { name: "Save" });
      expect(saveButton).not.toBeInTheDocument();
    });
  });
});

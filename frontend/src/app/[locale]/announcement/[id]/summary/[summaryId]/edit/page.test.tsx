import { render, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import AnnouncementSummaryEditPage from "src/app/[locale]/announcement/[id]/summary/[summaryId]/edit/page";

const mockUseActionState = jest.fn();
const mockGetAnnouncement = jest.fn().mockResolvedValue({
  data: {
    announcement_id: "opportunity-123",
    forecast_summary: { announcement_summary_id: "summary-1" },
  },
});

jest.mock(
  "src/app/[locale]/announcement/[id]/summary/[summaryId]/actions",
  () => ({
    announcementEditFormAction: () => {},
  }),
);

jest.mock("react", () => ({
  ...jest.requireActual<typeof import("react")>("react"),
  useActionState: () => mockUseActionState() as unknown,
}));

jest.mock("src/services/fetch/fetchers/grantorAnnouncementFetcher", () => ({
  getAnnouncement: (arg: unknown): unknown =>
    mockGetAnnouncement(arg) as unknown,
}));

const pageParams = new Promise<{ id: string; summaryId: string }>((resolve) => {
  resolve({ id: "opportunity-123", summaryId: "summary-1" });
});

// Jest for some reason thinks that any async child of this page must be a client component?
// disabling for now
describe("AnnouncementSummaryEditPage - action buttons", () => {
  beforeEach(() => {
    mockUseActionState.mockReturnValue([
      { validationErrors: {} },
      jest.fn(),
      false,
    ]);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("passes accessibility scan", async () => {
    const { container } = render(
      <AnnouncementSummaryEditPage params={pageParams} />,
    );
    const results = await waitFor(() => axe(container));

    expect(results).toHaveNoViolations();
  });
  // it("renders the save button", async () => {
  //   const component = await AnnouncementSummaryEditPage({ params: pageParams });
  //   render(component);
  //   expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  // });

  // it("calls the form action when save is clicked", async () => {
  //   const mockFormAction = jest.fn();
  //   mockUseActionState.mockReturnValue([
  //     { validationErrors: {} },
  //     mockFormAction,
  //     false,
  //   ]);

  //   const component = await AnnouncementSummaryEditPage({ params: pageParams });
  //   render(component);

  //   fireEvent.click(screen.getByRole("button", { name: "Save" }));

  //   expect(mockFormAction).toHaveBeenCalledTimes(1);
  // });
});

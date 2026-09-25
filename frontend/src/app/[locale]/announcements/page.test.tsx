import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import { identity } from "lodash";
import AnnouncementsListPage from "src/app/[locale]/announcements/page";
import { MissingAuthError, UnauthorizedError } from "src/errors";
import { AnnouncementListItem } from "src/types/announcement/announcementResponseTypes";
import { UserSession } from "src/types/authTypes";
import { LocalizedPageProps } from "src/types/intl";
import { FeatureFlaggedPageWrapper } from "src/types/uiTypes";
import { localeParams, useTranslationsMock } from "src/utils/testing/intlMocks";

import { FunctionComponent, ReactNode } from "react";

type onEnabled = (props: LocalizedPageProps) => ReactNode;

jest.mock("react", () => ({
  ...jest.requireActual<typeof import("react")>("react"),
  use: jest.fn(() => ({
    locale: "en",
  })),
}));

jest.mock("next-intl", () => ({
  useTranslations: () => useTranslationsMock(),
}));

jest.mock("next-intl/server", () => ({
  getTranslations: identity,
}));

const withFeatureFlagMock = jest
  .fn()
  .mockImplementation(
    (
      WrappedComponent: FunctionComponent<LocalizedPageProps>,
      _featureFlagName: string,
      _onEnabled: onEnabled,
    ) =>
      (props: { params: Promise<{ locale: string }> }) =>
        WrappedComponent(props) as unknown,
  );

jest.mock("src/services/featureFlags/withFeatureFlag", () => ({
  __esModule: true,
  default:
    (
      WrappedComponent: FunctionComponent<LocalizedPageProps>,
      featureFlagName: string,
      onEnabled: onEnabled,
    ) =>
    (props: LocalizedPageProps) =>
      (
        withFeatureFlagMock as FeatureFlaggedPageWrapper<
          LocalizedPageProps,
          ReactNode
        >
      )(
        WrappedComponent,
        featureFlagName,
        onEnabled,
      )(props) as FunctionComponent<LocalizedPageProps>,
}));

const redirectMock = jest.fn();

jest.mock("next/navigation", () => ({
  redirect: (location: string) => redirectMock(location) as unknown,
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/announcements",
  useSearchParams: () => new URLSearchParams("page=1"),
}));

const userSession: UserSession = {
  token: "fake token",
  user_id: "fake_user_id",
  session_duration_minutes: 15,
};

const mockSearchForAnnouncements = jest.fn().mockResolvedValue({
  data: [],
  pagination_info: { total_pages: 0, total_records: 0 },
});
const mockGetSession = jest.fn().mockResolvedValue(userSession);

jest.mock("src/services/fetch/fetchers/grantorAnnouncementFetcher", () => ({
  searchAccessibleAnnouncements: (arg: unknown): unknown =>
    mockSearchForAnnouncements(arg) as Promise<AnnouncementListItem[]>,
}));

jest.mock("src/services/auth/session", () => ({
  getSession: () => mockGetSession() as Promise<UserSession>,
}));

jest.mock("src/app/[locale]/error/page", () => ({
  TopLevelError: () => (
    <div>
      <span>Top Level Error</span>
    </div>
  ),
}));

const baseAnnouncement: AnnouncementListItem = {
  announcement_id: "89a44d32-0d90-4514-85a9-d5491f1c454d",
  announcement_title: "Test Announcement",
  announcement_number: "FO-26-00001",
  created_at: "2024-04-29T06:43:00Z",
  updated_at: "2024-04-29T06:43:00Z",
  forecast_summary: null,
  non_forecast_summary: {
    close_timestamp: null,
    is_forecast: false,
    post_timestamp: "2024-04-29T06:43:00Z",
    archive_timestamp: null,
    funding_instruments: [],
  },
};

describe("Announcements", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    withFeatureFlagMock.mockImplementation(
      (
        WrappedComponent: FunctionComponent<LocalizedPageProps>,
        _featureFlagName: string,
        _onEnabled: () => void,
      ) =>
        (props: { params: Promise<{ locale: string }> }) =>
          WrappedComponent(props) as unknown,
    );
  });

  it("renders no announcements message when list is empty", async () => {
    const component = await AnnouncementsListPage({ params: localeParams });
    render(component);

    expect(await screen.findByText("primary")).toBeVisible();
  });

  it("passes accessibility scan", async () => {
    const component = await AnnouncementsListPage({ params: localeParams });
    const { container } = render(component);
    const results = await waitFor(() => axe(container));

    expect(results).toHaveNoViolations();
  });

  it("renders announcements from backend contract fields", async () => {
    mockSearchForAnnouncements.mockResolvedValue({
      data: [baseAnnouncement],
      pagination_info: { total_pages: 1, total_records: 1 },
    });

    const component = await AnnouncementsListPage({ params: localeParams });
    render(component);

    expect(await screen.findByText("Test Announcement")).toBeVisible();
    expect(await screen.findByText("FO-26-00001")).toBeVisible();
    expect(mockSearchForAnnouncements).toHaveBeenCalled();
  });

  it("renders announcement count", async () => {
    mockSearchForAnnouncements.mockResolvedValue({
      data: [baseAnnouncement],
      pagination_info: { total_pages: 1, total_records: 1 },
    });

    const component = await AnnouncementsListPage({ params: localeParams });
    render(component);

    expect(await screen.findByText("numAnnouncements")).toBeVisible();
  });

  it("redirects to last page when out of range", async () => {
    mockSearchForAnnouncements.mockResolvedValue({
      data: [],
      pagination_info: { total_pages: 1, total_records: 7 },
    });

    await AnnouncementsListPage({
      params: localeParams,
      searchParams: Promise.resolve({ page: "2" }),
    });

    expect(redirectMock).toHaveBeenCalledWith("?page=1");
  });

  it("renders create announcement button", async () => {
    const component = await AnnouncementsListPage({ params: localeParams });
    render(component);

    const createAnnouncementLink = screen.getByRole("link", {
      name: "createAnnouncementButton",
    });
    expect(createAnnouncementLink).toBeVisible();
    expect(createAnnouncementLink).toHaveAttribute(
      "href",
      "/announcements/create",
    );
  });

  it("renders unauthenticated page for missing auth", async () => {
    mockSearchForAnnouncements.mockRejectedValue(
      new MissingAuthError("missing auth"),
    );

    const component = await AnnouncementsListPage({ params: localeParams });
    render(component);

    expect(await screen.findByText("unauthenticated")).toBeVisible();
  });

  it("renders error alert for general fetch errors", async () => {
    mockSearchForAnnouncements.mockRejectedValue(new Error("failure"));
    const component = await AnnouncementsListPage({ params: localeParams });
    render(component);

    expect(await screen.findByTestId("alert")).toBeVisible();
  });

  it("rethrows UnauthorizedError (401 unauthenticated) errors", async () => {
    mockSearchForAnnouncements.mockRejectedValue(
      new UnauthorizedError("No active session"),
    );

    await expect(
      AnnouncementsListPage({
        params: localeParams,
      }),
    ).rejects.toThrow(UnauthorizedError);
  });

  it("shows forecasted status tag for forecast announcements", async () => {
    mockSearchForAnnouncements.mockResolvedValue({
      data: [
        {
          ...baseAnnouncement,
          forecast_summary: {
            ...baseAnnouncement.non_forecast_summary,
            is_forecast: true,
          },
          non_forecast_summary: null,
        },
      ],
      pagination_info: { total_pages: 1, total_records: 1 },
    });

    const component = await AnnouncementsListPage({ params: localeParams });
    render(component);

    expect(
      await screen.findByTestId("announcement-status-forecasted"),
    ).toBeVisible();

    const popoverButton = screen.getByRole("button", { expanded: false });
    fireEvent.click(popoverButton);

    expect(screen.getByText(/actionButtons.edit/i)).toBeInTheDocument();
  });

  it("shows posted status tag for active announcements", async () => {
    mockSearchForAnnouncements.mockResolvedValue({
      data: [baseAnnouncement],
      pagination_info: { total_pages: 1, total_records: 1 },
    });

    const component = await AnnouncementsListPage({ params: localeParams });
    render(component);

    expect(
      await screen.findByTestId("announcement-status-posted"),
    ).toBeVisible();

    const viewLink = "/announcement/" + baseAnnouncement.announcement_id;
    const announcementTitleLink = screen.getByRole("link", {
      name: "Test Announcement",
    });
    expect(announcementTitleLink).toHaveAttribute("href", viewLink);

    const popoverButton = screen.getByRole("button", { expanded: false });
    fireEvent.click(popoverButton);

    expect(screen.getByText(/actionButtons.edit/i)).toBeInTheDocument();
  });
});

import { render, screen, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import OpportunityCompetitionPage from "src/app/[locale]/announcement/[id]/application-package/page";
import { MissingAuthError } from "src/errors";
import { GrantorAnnouncementDetail } from "src/types/announcement/announcementResponseTypes";
import { DeepPartial } from "src/utils/testing/commonTestUtils";
import { useTranslationsMock } from "src/utils/testing/intlMocks";

const testOpportunityId = "opp-abc-123";
const pageParams = Promise.resolve({ id: testOpportunityId, locale: "en" });

jest.mock("next-intl", () => ({
  useTranslations: () => useTranslationsMock(),
}));

jest.mock("next-intl/server", () => ({
  getTranslations: () => Promise.resolve((key: string) => key),
}));

jest.mock("next/navigation", () => ({
  notFound: jest.fn(),
  redirect: jest.fn(),
}));

jest.mock("src/services/featureFlags/withFeatureFlag", () => ({
  __esModule: true,
  default: (WrappedComponent: React.FunctionComponent) => (props: unknown) =>
    WrappedComponent(props as never),
}));

jest.mock(
  "src/components/grantor-announcements/AnnouncementDetailsHeader",
  () => ({
    AnnouncementDetailsHeader: () => (
      <div data-testid="opportunity-details-header" />
    ),
  }),
);

jest.mock(
  "src/app/[locale]/announcement/[id]/application-package/_components/ApplicationPackageForm",
  () => ({
    ApplicationPackageForm: ({
      competition,
    }: {
      competition?: { competition_id?: string };
    }) => (
      <div
        data-testid="competition-form"
        data-competition-id={competition?.competition_id ?? ""}
      />
    ),
  }),
);

const mockGetAnnouncement = jest.fn();
const mockCreateCompetitionForGrantor = jest.fn();
const mockAllForms = jest.fn();
const mockApplicationPackageForms = jest.fn();

jest.mock("src/services/fetch/fetchers/grantorAnnouncementFetcher", () => ({
  getAnnouncement: (...args: unknown[]) =>
    mockGetAnnouncement(...args) as unknown,
}));

jest.mock("src/services/fetch/fetchers/allFormsFetcher", () => ({
  getForms: (...args: unknown[]) => mockAllForms(...args) as unknown,
}));

const baseOpportunityData: DeepPartial<GrantorAnnouncementDetail> = {
  opportunity_id: "opp-abc-123",
  opportunity_title: "Test Opportunity",
  application_packages: null,
};

describe("OpportunityCompetitionPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("when opportunity has no existing competition", () => {
    beforeEach(() => {
      mockGetAnnouncement.mockResolvedValue({
        data: { ...baseOpportunityData, application_packages: null },
      });
      mockCreateCompetitionForGrantor.mockResolvedValue({
        data: { competition_id: "new-competition-id" },
      });
      mockApplicationPackageForms.mockResolvedValue({
        data: [],
      });
      mockAllForms.mockResolvedValue({
        data: [
          {
            current_version: {
              legacy_form_version: "2.1",
              major_version: 4,
              minor_version: 0,
            },
            form_id: "123e4567-e89b-12d3-a456-426614174000",
            name: "Application for Federal Assistance",
            short_name: "SF-424",
          },
        ],
      });
    });

    it("passes an empty string to ApplicationPackageForm", async () => {
      const component = await OpportunityCompetitionPage({
        params: pageParams,
      });
      render(component);

      expect(screen.getByTestId("competition-form")).toHaveAttribute(
        "data-competition-id",
        "",
      );
    });

    it("passes accessibility scan", async () => {
      const component = await OpportunityCompetitionPage({
        params: pageParams,
      });
      const { container } = render(component);
      const results = await waitFor(() => axe(container));

      expect(results).toHaveNoViolations();
    });
  });

  describe("when opportunity already has a competition", () => {
    beforeEach(() => {
      mockGetAnnouncement.mockResolvedValue({
        data: {
          ...baseOpportunityData,
          application_packages: [{ competition_id: "existing-competition-id" }],
        },
      });
    });

    it("passes the existing competition_id to ApplicationPackageForm", async () => {
      const component = await OpportunityCompetitionPage({
        params: pageParams,
      });
      render(component);

      expect(screen.getByTestId("competition-form")).toHaveAttribute(
        "data-competition-id",
        "existing-competition-id",
      );
    });

    it("passes accessibility scan", async () => {
      const component = await OpportunityCompetitionPage({
        params: pageParams,
      });
      const { container } = render(component);
      const results = await waitFor(() => axe(container));

      expect(results).toHaveNoViolations();
    });
  });

  describe("MissingAuthError handling", () => {
    it("returns UnauthorizedMessage when getAnnouncement throws MissingAuthError", async () => {
      mockGetAnnouncement.mockRejectedValue(
        new MissingAuthError("Missing auth"),
      );
      const component = await OpportunityCompetitionPage({
        params: pageParams,
      });
      render(component);
      expect(screen.getByTestId("alert")).toBeVisible();
    });
  });
});

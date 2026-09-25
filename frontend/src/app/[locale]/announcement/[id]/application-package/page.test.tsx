import { render, screen, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import OpportunityApplicationPackagePage from "src/app/[locale]/announcement/[id]/application-package/page";
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
      applicationPackage,
    }: {
      applicationPackage?: { applicationPackage_id?: string };
    }) => (
      <div
        data-testid="applicationPackage-form"
        data-applicationPackage-id={
          applicationPackage?.applicationPackage_id ?? ""
        }
      />
    ),
  }),
);

const mockGetAnnouncement = jest.fn();
const mockCreateApplicationPackageForGrantor = jest.fn();
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

describe("OpportunityApplicationPackagePage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("when opportunity has no existing applicationPackage", () => {
    beforeEach(() => {
      mockGetAnnouncement.mockResolvedValue({
        data: { ...baseOpportunityData, application_packages: null },
      });
      mockCreateApplicationPackageForGrantor.mockResolvedValue({
        data: { applicationPackage_id: "new-applicationPackage-id" },
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
      const component = await OpportunityApplicationPackagePage({
        params: pageParams,
      });
      render(component);

      expect(screen.getByTestId("applicationPackage-form")).toHaveAttribute(
        "data-applicationPackage-id",
        "",
      );
    });

    it("passes accessibility scan", async () => {
      const component = await OpportunityApplicationPackagePage({
        params: pageParams,
      });
      const { container } = render(component);
      const results = await waitFor(() => axe(container));

      expect(results).toHaveNoViolations();
    });
  });

  describe("when opportunity already has a applicationPackage", () => {
    beforeEach(() => {
      mockGetAnnouncement.mockResolvedValue({
        data: {
          ...baseOpportunityData,
          application_packages: [
            { applicationPackage_id: "existing-applicationPackage-id" },
          ],
        },
      });
    });

    it("passes the existing applicationPackage_id to ApplicationPackageForm", async () => {
      const component = await OpportunityApplicationPackagePage({
        params: pageParams,
      });
      render(component);

      expect(screen.getByTestId("applicationPackage-form")).toHaveAttribute(
        "data-applicationPackage-id",
        "existing-applicationPackage-id",
      );
    });

    it("passes accessibility scan", async () => {
      const component = await OpportunityApplicationPackagePage({
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
      const component = await OpportunityApplicationPackagePage({
        params: pageParams,
      });
      render(component);
      expect(screen.getByTestId("alert")).toBeVisible();
    });
  });
});

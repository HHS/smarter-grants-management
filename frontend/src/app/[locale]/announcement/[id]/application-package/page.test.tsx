import { render, screen, waitFor } from "@testing-library/react";
import { axe } from "jest-axe";
import AnnouncementApplicationPackagePage from "src/app/[locale]/announcement/[id]/application-package/page";
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
      applicationPackage?: { application_package_id?: string };
    }) => (
      <div
        data-testid="application-package-form"
        data-application-package-id={
          applicationPackage?.application_package_id ?? ""
        }
      />
    ),
  }),
);

const mockGetAnnouncement = jest.fn();
const mockGetApplicationPackage = jest.fn();
const mockCreateApplicationPackage = jest.fn();
const mockAllForms = jest.fn();
const mockApplicationPackageForms = jest.fn();

jest.mock("src/services/fetch/fetchers/grantorAnnouncementFetcher", () => ({
  getAnnouncement: (...args: unknown[]) =>
    mockGetAnnouncement(...args) as unknown,
  getApplicationPackage: (...args: unknown[]) =>
    mockGetApplicationPackage(...args) as unknown,
}));

jest.mock("src/services/fetch/fetchers/allFormsFetcher", () => ({
  getForms: (...args: unknown[]) => mockAllForms(...args) as unknown,
}));

const baseOpportunityData: DeepPartial<GrantorAnnouncementDetail> = {
  opportunity_id: "opp-abc-123",
  opportunity_title: "Test Opportunity",
  application_packages: null,
};

describe("AnnouncementApplicationPackagePage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("when opportunity has no existing application package", () => {
    beforeEach(() => {
      mockGetAnnouncement.mockResolvedValue({
        data: { ...baseOpportunityData, application_packages: null },
      });
      mockCreateApplicationPackage.mockResolvedValue({
        data: { application_package_id: "new-application-package-id" },
      });
      mockApplicationPackageForms.mockResolvedValue({
        data: [],
      });
      mockAllForms.mockResolvedValue({
        data: [
          {
            version: "4.0",
            form_id: 713,
            name: "Application for Federal Assistance",
            short_name: "SF-424",
          },
        ],
      });
    });

    it("passes an empty string to ApplicationPackageForm", async () => {
      const component = await AnnouncementApplicationPackagePage({
        params: pageParams,
      });
      render(component);

      expect(screen.getByTestId("application-package-form")).toHaveAttribute(
        "data-application-package-id",
        "",
      );
    });

    it("passes accessibility scan", async () => {
      const component = await AnnouncementApplicationPackagePage({
        params: pageParams,
      });
      const { container } = render(component);
      const results = await waitFor(() => axe(container));

      expect(results).toHaveNoViolations();
    });
  });

  describe("when opportunity already has an application package", () => {
    beforeEach(() => {
      mockGetAnnouncement.mockResolvedValue({
        data: {
          ...baseOpportunityData,
          application_packages: [
            { application_package_id: "existing-application-package-id" },
          ],
        },
      });
      mockGetApplicationPackage.mockResolvedValue({
        data: {
          application_package_id: "existing-application-package-id",
          application_package_instructions: [],
        },
      });
    });

    it("fetches the full application package and passes it to ApplicationPackageForm", async () => {
      const component = await AnnouncementApplicationPackagePage({
        params: pageParams,
      });
      render(component);

      expect(mockGetApplicationPackage).toHaveBeenCalledWith(
        "opp-abc-123",
        "existing-application-package-id",
      );
      expect(screen.getByTestId("application-package-form")).toHaveAttribute(
        "data-application-package-id",
        "existing-application-package-id",
      );
    });

    it("passes accessibility scan", async () => {
      const component = await AnnouncementApplicationPackagePage({
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
      const component = await AnnouncementApplicationPackagePage({
        params: pageParams,
      });
      render(component);
      expect(screen.getByTestId("alert")).toBeVisible();
    });
  });
});

import {
  ApiRequestError,
  MissingAuthError,
  parseErrorStatus,
} from "src/errors";
import { getAnnouncement } from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import { GrantorAnnouncementDetail } from "src/types/announcement/announcementResponseTypes";
import { computeAnnouncementPublishEligibility } from "src/utils/announcement/announcementPublishEligibility";
import { shouldDisableForecast } from "src/utils/announcement/announcementUtils";

import { getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";
import { Alert, GridContainer, Link } from "@trussworks/react-uswds";

import GeneralErrorAlert from "src/components/core/GeneralErrorAlert";
import { UnauthorizedMessage } from "src/components/core/UnauthorizedMessage";
import { AnnouncementDetailsHeader } from "src/components/grantor-announcements/AnnouncementDetailsHeader";
import { ProgressChecker } from "src/components/grantor-announcements/ProgressChecker";
import { OverviewButtons } from "./_components/OverviewButtons";
import {
  applicationPackageRequiredFields,
  summaryRequiredFields,
} from "./RequiredFields";

type PageProps = {
  params: Promise<{ id: string; locale: string }>;
  searchParams?: Promise<Record<string, string>>;
};

const SummaryLink = ({
  summaryId,
  isForecast,
  announcementId,
  disable,
}: {
  summaryId?: string;
  isForecast?: boolean;
  announcementId: string;
  disable?: boolean;
}) => {
  const linkTarget = summaryId
    ? `/announcement/${announcementId}/summary/${summaryId}/edit`
    : `/announcement/${announcementId}/summary/create/${isForecast ? "forecast" : "synopsis"}`;
  const linkText = isForecast ? "Forecast Summary" : "Synopsis Summary";
  return disable ? (
    <span>{linkText}</span>
  ) : (
    <Link href={linkTarget}>{linkText}</Link>
  );
};

export default async function OpportunityOverviewPage({
  params,
  searchParams,
}: PageProps) {
  const { id, locale } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const isNewlyCreated = resolvedSearchParams.fromCreate === "true";
  const t = await getTranslations({
    locale,
    namespace: "AnnouncementOverview",
  });
  const tHeader = await getTranslations({
    locale,
    namespace: "AnnouncementDetailsHeader",
  });

  let announcementData: GrantorAnnouncementDetail;
  try {
    const response = await getAnnouncement(id);
    announcementData = response.data;
  } catch (error) {
    if (error instanceof MissingAuthError) {
      return <UnauthorizedMessage />;
    }
    const status = parseErrorStatus(error as ApiRequestError);
    if (status === 404) {
      notFound();
    }
    if (status === 403) {
      return <UnauthorizedMessage />;
    }
    return (
      <GridContainer>
        <GeneralErrorAlert />
      </GridContainer>
    );
  }

  const applicationPackageUrl = "../" + id + "/application-package";
  let applicationPackage = {};
  if (
    announcementData.application_packages &&
    announcementData.application_packages.length > 0
  ) {
    // For now, use the first application package
    applicationPackage = announcementData.application_packages[0];
  }

  const publishEnabled = computeAnnouncementPublishEligibility();

  return (
    <div className="bg-white">
      <AnnouncementDetailsHeader
        announcementData={announcementData}
        locale={locale}
      >
        <OverviewButtons opportunityId={id} publishEnabled={publishEnabled} />
      </AnnouncementDetailsHeader>
      <div className="grid-container padding-top-4 padding-bottom-4">
        {isNewlyCreated && (
          <Alert
            type="success"
            heading={tHeader("alerts.newOpportunityHeading")}
            headingLevel="h3"
            className="margin-bottom-4"
          >
            {tHeader("alerts.newOpportunityBody")}
          </Alert>
        )}
        <div
          className="grid-row grid-gap-2 padding-top-2"
          data-testid="overview-row-edit"
        >
          <div className="tablet:grid-col">
            <SummaryLink
              announcementId={id}
              summaryId={
                announcementData.forecast_summary?.announcement_summary_id
              }
              isForecast={true}
              disable={shouldDisableForecast(announcementData)}
            />
          </div>
          <div className="tablet:grid-col">
            <ProgressChecker
              requiredFields={summaryRequiredFields}
              dataToCheck={announcementData.forecast_summary || {}}
            />
          </div>
        </div>
        <hr />
        <div
          className="grid-row grid-gap-2 padding-top-2"
          data-testid="overview-row-edit"
        >
          <div className="tablet:grid-col">
            <SummaryLink
              announcementId={id}
              summaryId={
                announcementData.non_forecast_summary?.announcement_summary_id
              }
              isForecast={false}
            />
          </div>
          <div className="tablet:grid-col">
            <ProgressChecker
              requiredFields={summaryRequiredFields}
              dataToCheck={announcementData.non_forecast_summary || {}}
            />
          </div>
        </div>
        <hr />
        <div
          className="grid-row grid-gap-2 padding-top-2"
          data-testid="overview-row-application-package"
        >
          <div className="tablet:grid-col">
            <Link href={applicationPackageUrl}>
              {t("labels.applicationPackageLink")}
            </Link>
          </div>
          <div className="tablet:grid-col">
            <ProgressChecker
              requiredFields={applicationPackageRequiredFields}
              dataToCheck={applicationPackage}
            />{" "}
          </div>
        </div>
        <hr />
      </div>
    </div>
  );
}

import {
  ApiRequestError,
  MissingAuthError,
  parseErrorStatus,
} from "src/errors";
import { getAnnouncement } from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import {
  GrantorAnnouncementDetail,
  Summary,
} from "src/types/announcement/announcementResponseTypes";
import { computeAnnouncementPublishEligibility } from "src/utils/announcement/announcementPublishEligibility";

import { getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";
import { Link } from "@trussworks/react-uswds";

import { UnauthorizedMessage } from "src/components/core/UnauthorizedMessage";
import { AnnouncementDetailsHeader } from "src/components/grantor-announcements/AnnouncementDetailsHeader";
import {
  getProgress,
  ProgressChecker,
} from "src/components/grantor-announcements/ProgressChecker";
import { OverviewButtons } from "./_components/OverviewButtons";
import {
  applicationPackageRequiredFields,
  summaryRequiredFields,
} from "./RequiredFields";

type PageProps = {
  params: Promise<{ id: string; locale: string }>;
  searchParams?: Promise<Record<string, string>>;
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
  let opportunityData: GrantorAnnouncementDetail;
  try {
    const response = await getAnnouncement(id);
    opportunityData = response.data;
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
    throw error;
  }
  const editUrl = "../" + id + "/edit";
  const applicationPackageUrl = "../" + id + "/application-package";
  const summary: Summary =
    opportunityData.summary ??
    opportunityData.non_forecast_summary ??
    opportunityData.forecast_summary;
  let applicationPackage = {};
  if (
    opportunityData.application_packages &&
    opportunityData.application_packages.length > 0
  ) {
    // For now, use the first application package
    applicationPackage = opportunityData.application_packages[0];
  }

  const summaryStatus = getProgress(summaryRequiredFields, summary);
  const applicationPackageStatus = getProgress(
    applicationPackageRequiredFields,
    applicationPackage,
  );

  // TODO(#251): re-enable once the backend implements POST /v1/announcements/{id}/publish
  const isPublishSupportedByBackend: boolean = false;
  const publishEnabled =
    isPublishSupportedByBackend &&
    computeAnnouncementPublishEligibility(
      opportunityData.is_draft,
      summaryStatus,
      applicationPackageStatus,
    );

  return (
    <div className="bg-white">
      <AnnouncementDetailsHeader
        opportunityData={opportunityData}
        locale={locale}
        isNewlyCreated={isNewlyCreated}
      >
        <OverviewButtons opportunityId={id} publishEnabled={publishEnabled} />
      </AnnouncementDetailsHeader>
      <div className="grid-container padding-top-4 padding-bottom-4">
        <div
          className="grid-row grid-gap-2 padding-top-2"
          data-testid="overview-row-edit"
        >
          <div className="tablet:grid-col">
            <Link href={editUrl}>{t("labels.editOpportunityLink")}</Link>
          </div>
          <div className="tablet:grid-col">
            <ProgressChecker
              requiredFields={summaryRequiredFields}
              dataToCheck={summary}
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

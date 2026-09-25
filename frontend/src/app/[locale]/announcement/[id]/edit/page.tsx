import AnnouncementEditForm from "src/app/[locale]/announcement/[id]/edit/_components/AnnouncementEditForm";
import {
  ApiRequestError,
  MissingAuthError,
  parseErrorStatus,
} from "src/errors";
import { getAnnouncement } from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import { GrantorAnnouncementDetail } from "src/types/announcement/announcementResponseTypes";
import { buildAnnouncementEditInitialValues } from "src/utils/announcementEditFormConfig";

import { getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";
import { Alert, Button, GridContainer } from "@trussworks/react-uswds";

import LeftHandFormNav from "src/components/core/forms/LeftHandFormNav";
import GeneralErrorAlert from "src/components/core/GeneralErrorAlert";
import { UnauthorizedMessage } from "src/components/core/UnauthorizedMessage";
import { AnnouncementDetailsHeader } from "src/components/grantor-announcements/AnnouncementDetailsHeader";

export const dynamic = "force-dynamic";

const HeaderButtons = ({ saveAndExitLabel }: { saveAndExitLabel: string }) => {
  return (
    <>
      <Button
        type="submit"
        form="announcement-edit-form"
        className="margin-left-1"
      >
        {saveAndExitLabel}
      </Button>
    </>
  );
};

type PageProps = {
  params: Promise<{ id: string; locale: string }>;
};

export default async function AnnouncementEditPage({ params }: PageProps) {
  const { id, locale } = await params;
  const t = await getTranslations({ locale, namespace: "Errors" });
  const tEdit = await getTranslations({ locale, namespace: "OpportunityEdit" });

  // TODO(#8601): Replace this fail-closed placeholder with a real grantor authorization
  // check once the frontend has a way to verify whether the current session can edit
  // this opportunity for its agency.
  const hasVerifiedGrantorEditAccess = true;

  let announcementData: GrantorAnnouncementDetail;
  let announcementSummaryId: string;
  try {
    const response = await getAnnouncement(id);
    announcementData = response.data;
    announcementSummaryId =
      response.data.forecast_summary?.announcement_summary_id ??
      response.data.non_forecast_summary?.announcement_summary_id ??
      "";
  } catch (error) {
    if (error instanceof MissingAuthError) {
      // TODO: should be an anauthenticated message
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

  if (id !== announcementData.announcement_id) {
    return (
      <GridContainer className="margin-top-4">
        <Alert type="error" heading={t("heading")} headingLevel="h4">
          {t("genericMessage")}
        </Alert>
      </GridContainer>
    );
  }

  if (!hasVerifiedGrantorEditAccess) {
    return <UnauthorizedMessage />;
  }

  const activeSummary =
    announcementData.forecast_summary ??
    announcementData.non_forecast_summary ??
    announcementData.summary;
  const initialValues = buildAnnouncementEditInitialValues({
    ...announcementData,
    attachments: [],
    summary: activeSummary,
  });
  const navigationItems = [
    { text: tEdit("sections.fundingDetails"), href: "funding-details" },
    { text: tEdit("sections.eligibility"), href: "eligibility" },
    {
      text: tEdit("sections.additionalInformation"),
      href: "additional-information",
    },
    { text: tEdit("sections.attachments"), href: "attachments" },
  ];
  return (
    <div className="bg-white">
      <AnnouncementDetailsHeader
        opportunityData={announcementData}
        locale={locale}
        hasBackToOverview={true}
      >
        <HeaderButtons saveAndExitLabel={tEdit("button.saveAndExit")} />
      </AnnouncementDetailsHeader>

      <div className="grid-container padding-bottom-4">
        <div className="usa-in-page-nav-container">
          <LeftHandFormNav title={tEdit("navTitle")} fields={navigationItems} />

          <section className="order-2 width-full maxw-tablet-xl padding-top-4">
            <AnnouncementEditForm
              announcementId={announcementData.announcement_id}
              announcementSummaryId={announcementSummaryId}
              isForecast={!!announcementData.forecast_summary}
              initialValues={initialValues}
              initialAttachments={announcementData.attachments ?? []}
            />
          </section>
        </div>
      </div>
    </div>
  );
}

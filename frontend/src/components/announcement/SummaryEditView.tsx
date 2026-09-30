import AnnouncementEditForm from "src/components/SummaryEditView/AnnouncementEditForm";
import {
  ApiRequestError,
  MissingAuthError,
  parseErrorStatus,
} from "src/errors";
import { getAnnouncement } from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import { GrantorAnnouncementDetail } from "src/types/announcement/announcementResponseTypes";
import { buildAnnouncementEditInitialValues } from "src/utils/announcementEditFormConfig";

import { notFound } from "next/navigation";
import { Alert, Button, GridContainer } from "@trussworks/react-uswds";

import LeftHandFormNav from "src/components/core/forms/LeftHandFormNav";
import GeneralErrorAlert from "src/components/core/GeneralErrorAlert";
import { UnauthorizedMessage } from "src/components/core/UnauthorizedMessage";
import { AnnouncementDetailsHeader } from "src/components/grantor-announcements/AnnouncementDetailsHeader";

type SummaryEditViewProps = {
  summaryId?: string; // we may want this later to support multiple summaries
  announcementId: string;
  isForecast: boolean;
};

// TODO(#8601): Replace this fail-closed placeholder with a real grantor authorization
// check once the frontend has a way to verify whether the current session can edit
// this opportunity for its agency.
const hasVerifiedGrantorEditAccess = true;

const navigationItems = [
  { text: "Funding details", href: "funding-details" },
  { text: "Eligibility", href: "eligibility" },
  {
    text: "Additional information",
    href: "additional-information",
  },
  { text: "Attachments", href: "attachments" },
];

export default async function SummaryEditView({
  announcementId,
  isForecast,
}: SummaryEditViewProps) {
  let announcementData: GrantorAnnouncementDetail;
  let announcementSummaryId: string;
  try {
    const response = await getAnnouncement(announcementId);
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

  if (announcementId !== announcementData.announcement_id) {
    return (
      <GridContainer className="margin-top-4">
        <Alert type="error" heading="We're sorry." headingLevel="h4">
          There seems to have been an error.
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
  return (
    <div className="bg-white">
      <AnnouncementDetailsHeader
        opportunityData={announcementData}
        locale={"en"}
        hasBackToOverview={true}
      >
        <Button
          type="submit"
          form="announcement-edit-form"
          className="margin-left-1"
        >
          Save
        </Button>
      </AnnouncementDetailsHeader>

      <div className="grid-container padding-bottom-4">
        <div className="usa-in-page-nav-container">
          <LeftHandFormNav title="On this page" fields={navigationItems} />

          <section className="order-2 width-full maxw-tablet-xl padding-top-4">
            <AnnouncementEditForm
              announcementId={announcementData.announcement_id}
              announcementSummaryId={announcementSummaryId}
              isForecast={isForecast}
              initialValues={initialValues}
              initialAttachments={
                announcementData.announcement_attachments ?? []
              }
            />
          </section>
        </div>
      </div>
    </div>
  );
}

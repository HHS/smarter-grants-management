import {
  ApiRequestError,
  MissingAuthError,
  parseErrorStatus,
} from "src/errors";
import { getAnnouncement } from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import {
  AnnouncementSummaryDetail,
  GrantorAnnouncementDetail,
} from "src/types/announcement/announcementResponseTypes";
import { buildAnnouncementEditInitialValues } from "src/utils/announcementEditFormConfig";

import { notFound } from "next/navigation";
import { Alert, Button, GridContainer } from "@trussworks/react-uswds";

import LeftHandFormNav from "src/components/core/forms/LeftHandFormNav";
import GeneralErrorAlert from "src/components/core/GeneralErrorAlert";
import { UnauthorizedMessage } from "src/components/core/UnauthorizedMessage";
import { AnnouncementDetailsHeader } from "src/components/grantor-announcements/AnnouncementDetailsHeader";
import AnnouncementEditForm from "src/components/SummaryEditView/AnnouncementEditForm";

type SummaryEditViewProps = {
  summaryId?: string; // we may want this later to support multiple summaries
  announcementId: string;
  isForecast?: boolean;
  createMode?: boolean;
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

const GenericErrorDisplay = () => (
  <GridContainer className="margin-top-4">
    <Alert type="error" heading="We're sorry." headingLevel="h4">
      There seems to have been an error.
    </Alert>
  </GridContainer>
);

// makes sure we are editing / creating the right type of summary
const validateProperState = ({
  announcementId,
  summaryId,
  isForecast,
  createMode,
  announcementData,
}: {
  announcementData: GrantorAnnouncementDetail;
} & SummaryEditViewProps): boolean => {
  if (announcementId !== announcementData.announcement_id) {
    console.error(
      "Announcement id does not match id from fetched announcement",
    );
    return true;
  }

  if (createMode) {
    if (isForecast && announcementData.forecast_summary) {
      console.error("Forecast summary already exists");
      return true;
    }
    if (!isForecast && announcementData.non_forecast_summary) {
      console.error("Synopsis already exists");
      return true;
    }
  }
  if (isForecast && !announcementData.forecast_summary) {
    console.error(
      "Attempting to edit forecast summary on announcement where one doesn't exist yet",
    );
    return true;
  }

  if (!isForecast && !announcementData.non_forecast_summary) {
    console.error(
      "Attempting to edit synopsis summary on announcement where one doesn't exist yet",
    );
    return true;
  }

  if (
    isForecast &&
    announcementData.forecast_summary?.announcement_summary_id !== summaryId &&
    !isForecast &&
    announcementData.non_forecast_summary?.announcement_summary_id !== summaryId
  ) {
    console.error(
      "Announcement summary id does not match id from fetched announcement",
    );
    return true;
  }
  return false;
};

const getActiveSummary = (
  createMode: boolean,
  isForecast: boolean,
  announcemenData: GrantorAnnouncementDetail,
): AnnouncementSummaryDetail | object => {
  if (createMode) {
    return {};
  }
  if (isForecast) {
    if (!announcemenData.forecast_summary) {
      console.error("No active forecast summary");
      return {};
    }
    return announcemenData.forecast_summary;
  }
  if (!announcemenData.non_forecast_summary) {
    console.error("No active synopsis summary");
    return {};
  }
  return announcemenData.non_forecast_summary;
};

export default async function SummaryEditView({
  announcementId,
  summaryId,
  isForecast = false,
  createMode = false,
}: SummaryEditViewProps) {
  let announcementData: GrantorAnnouncementDetail;
  try {
    const response = await getAnnouncement(announcementId);
    announcementData = response.data;
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

  const stateValidationError = validateProperState({
    announcementId,
    summaryId,
    isForecast,
    createMode,
    announcementData,
  });

  if (stateValidationError) {
    return <GenericErrorDisplay />;
  }

  if (!hasVerifiedGrantorEditAccess) {
    return <UnauthorizedMessage />;
  }

  const activeSummary = getActiveSummary(
    createMode,
    isForecast,
    announcementData,
  );

  const initialValues = buildAnnouncementEditInitialValues(
    {
      ...announcementData,
      attachments: [],
      summary: activeSummary,
    },
    createMode,
  );

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
              announcementId={announcementId}
              announcementSummaryId={
                createMode
                  ? ""
                  : (activeSummary as AnnouncementSummaryDetail)
                      .announcement_summary_id
              }
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

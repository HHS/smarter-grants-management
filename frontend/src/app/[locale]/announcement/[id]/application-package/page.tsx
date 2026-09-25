import { ApplicationPackageForm } from "src/app/[locale]/announcement/[id]/application-package/_components/ApplicationPackageForm";
import {
  ApiRequestError,
  MissingAuthError,
  parseErrorStatus,
} from "src/errors";
import { getForms } from "src/services/fetch/fetchers/allFormsFetcher";
import { getAnnouncement } from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import { ApplicationPackage } from "src/types/applicationPackageResponseTypes";

import { useTranslations } from "next-intl";
import { getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";
import { Button } from "@trussworks/react-uswds";

import LeftHandFormNav from "src/components/core/forms/LeftHandFormNav";
import { UnauthorizedMessage } from "src/components/core/UnauthorizedMessage";
import { AnnouncementDetailsHeader } from "src/components/grantor-announcements/AnnouncementDetailsHeader";

type PageProps = {
  params: Promise<{ id: string; locale: string }>;
};

export const dynamic = "force-dynamic";

// We are temporarily removing the SF-424 Short form, pending implementation of form libraries
// If any other forms need to be blocked, add them to this array
const blockedForms = ["cf355a4d-d840-43fd-a78f-729edf41ab4c"];

const ButtonSaveAndExit = () => {
  const t = useTranslations("OpportunityCompetition");
  return (
    <>
      <Button
        type="submit"
        form="opportunity-applicationPackage-form"
        className="margin-left-1"
      >
        {t("button.saveAndExit")}
      </Button>
    </>
  );
};

export default async function OpportunityApplicationPackagePage({
  params,
}: PageProps) {
  const { id, locale } = await params;
  const forms = await getForms();
  forms.data = forms.data.filter((form) => {
    return !blockedForms.includes(form.form_id);
  });
  const t = await getTranslations({
    locale,
    namespace: "OpportunityCompetition",
  });

  let opportunityData;
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

  // NOTE: Currently we are only supporting a single applicationPackage
  let applicationPackage: ApplicationPackage | undefined = undefined;
  if (opportunityData.application_packages?.[0]) {
    applicationPackage = opportunityData.application_packages[0];
  }

  const navigationItems = [
    {
      text: t("applicationRequirements"),
      href: "application-requirements",
    },
    {
      text: t("sectionSubmissionSetUp.header"),
      href: "submission-set-up",
    },
    {
      text: t("sectionSubmissionWindow.header"),
      href: "submission-window",
    },
    {
      text: t("sectionAgencyContact.header"),
      href: "agency-contact",
    },
    {
      text: t("sectionApplicationInstructions.header"),
      href: "application-instructions",
    },
    {
      text: t("sectionRequiredForms.header"),
      href: "required-forms",
    },
    {
      text: t("sectionApplicationChecklist.header"),
      href: "application-checklist",
    },
    {
      text: t("sectionNarrativeFormatInstructions.header"),
      href: "narrative-format-instructions",
    },
  ];

  return (
    <div className="bg-white">
      <AnnouncementDetailsHeader
        opportunityData={opportunityData}
        locale={locale}
        hasBackToOverview={true}
      >
        <ButtonSaveAndExit />
      </AnnouncementDetailsHeader>

      <div className="grid-container padding-bottom-4">
        <div className="usa-in-page-nav-container">
          <LeftHandFormNav title={t("leftNavTitle")} fields={navigationItems} />

          <section className="order-2 width-full maxw-tablet-xl padding-top-4">
            <ApplicationPackageForm
              announcementId={id}
              applicationPackage={applicationPackage}
              forms={forms.data}
            />
          </section>
        </div>
      </div>
    </div>
  );
}

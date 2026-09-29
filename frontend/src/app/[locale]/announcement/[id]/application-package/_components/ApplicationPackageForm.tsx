"use client";

import { AgencyContact } from "src/app/[locale]/announcement/[id]/application-package/_components/sections/AgencyContact";
import { ApplicationInstructions } from "src/app/[locale]/announcement/[id]/application-package/_components/sections/ApplicationInstructions";
import { RequiredForms } from "src/app/[locale]/announcement/[id]/application-package/_components/sections/RequiredForms";
import { SubmissionSetUp } from "src/app/[locale]/announcement/[id]/application-package/_components/sections/SubmissionSetUp";
import { SubmissionWindow } from "src/app/[locale]/announcement/[id]/application-package/_components/sections/SubmissionWindow";
import {
  ApplicationPackageActionState,
  applicationPackageFormAction,
} from "src/app/[locale]/announcement/[id]/application-package/actions";
import { FormType } from "src/types/allFormsResponseTypes";
import {
  ApplicationPackage,
  ApplicationPackageFormsSubmitApi,
} from "src/types/applicationPackageResponseTypes";
import { UploadFileMetadata } from "src/types/fileUploadTypes";

import { useTranslations } from "next-intl";
import React, { useEffect, useRef, useState } from "react";
import {
  Alert,
  Button,
  ModalRef,
  ModalToggleButton,
} from "@trussworks/react-uswds";

import { FormSelectModal } from "./FormSelectModal";

// SF 424. As we start to support other form families, this will be replaced with a more complex function
const alwaysRequiredForms: Record<string, boolean> = {
  "1623b310-85be-496a-b84b-34bdee22a68a": true,
};
type ApplicationPackageFormProps = {
  announcementId: string;
  applicationPackage?: ApplicationPackage;
  forms: FormType[];
};

export function ApplicationPackageForm({
  announcementId,
  applicationPackage,
  forms,
}: ApplicationPackageFormProps) {
  const t = useTranslations("OpportunityCompetition");

  const applicationPackageId: string =
    applicationPackage?.applicationPackage_id || "";
  const existingFiles: UploadFileMetadata[] =
    applicationPackage?.applicationPackage_instructions.map((instruction) => ({
      id: instruction.applicationPackage_instruction_id,
      fileName: instruction.file_name,
      updatedAt: instruction.updated_at,
      downloadUrl: instruction.download_path,
    })) ?? [];

  // ===== Required Forms =====
  const formModalRef = useRef<ModalRef | null>(null);
  const [requiredForms, setRequiredForms] =
    useState<ApplicationPackageFormsSubmitApi>(
      applicationPackage?.applicationPackage_forms?.map(
        ({ form, is_required }) => ({
          form_id: form.form_id,
          is_required,
        }),
      ) ??
        Object.entries(alwaysRequiredForms).map(([formId, isRequired]) => ({
          form_id: formId,
          is_required: isRequired,
        })),
    );

  // ===== Server side action to save data =====
  const [formState, setFormState] = useState<ApplicationPackageActionState>({});
  const [isPending, setIsPending] = useState(false);

  useEffect(() => {
    if (
      formState.validationErrors &&
      Object.keys(formState.validationErrors).length
    ) {
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }
  }, [formState.validationErrors]);

  const handleSubmit = (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsPending(true);

    // 1. Dynamically get the route and bind to the server action
    // The default route is triggered by the saveAndExit button in the header component
    const submitterButton = event.nativeEvent.submitter;
    const submitType = submitterButton?.dataset.submitType || "saveAndExit";
    const saveDataAndRoute = applicationPackageFormAction.bind(
      null,
      submitType,
      requiredForms, // objects cannot be placed in hidden inputs
    );

    // 2. Execute manually (FormData must be explicitly passed as the final argument)
    const formData = new FormData(event.currentTarget);
    saveDataAndRoute(formData)
      .then((result) => setFormState(result))
      .catch(() => setFormState({ errorMessage: t("alerts.networkError") }))
      .finally(() => setIsPending(false));
  };

  // ===== Render the form =====
  return (
    <form id="opportunity-applicationPackage-form" onSubmit={handleSubmit}>
      <input type="hidden" name="announcementId" value={announcementId} />
      <input
        type="hidden"
        name="applicationPackageId"
        value={applicationPackageId}
      />

      {formState.errorMessage ? (
        <div className="margin-top-2">
          <Alert
            type="warning"
            heading={formState.errorMessage}
            headingLevel="h3"
            validation
          />
        </div>
      ) : null}

      {formState.validationErrors &&
      Object.keys(formState.validationErrors).length > 0 ? (
        <div className="margin-top-2">
          <Alert
            type="error"
            heading={t("alerts.validationErrors")}
            headingLevel="h3"
          >
            <span className="display-block margin-top-1 margin-bottom-1">
              {t("alerts.validationErrorBody")}
            </span>
            {Array.from(
              new Set(Object.values(formState.validationErrors).flat()),
            ).map((error, i) => (
              <span key={i} className="display-block">
                {error}
              </span>
            ))}
          </Alert>
        </div>
      ) : null}

      <div className="bg-white">
        {/* TODO(#10507): remove minh-viewport once the applicationPackage page has enough content that sticky nav no longer releases */}
        <div className="grid-container padding-bottom-4 minh-viewport">
          <section className="order-2 width-full maxw-tablet-xl padding-top-4">
            <div
              id="application-requirements"
              className="padding-bottom-4 border-bottom border-base-lighter simpler-page-anchor-offset"
            >
              <h2 className="font-heading-xl margin-top-0 margin-bottom-1">
                {t("applicationRequirements")}
              </h2>
              <p className="font-body-lg text-base-dark margin-top-0">
                {t("applicationRequirementsSubheader")}
              </p>
              <SubmissionSetUp
                publicApplicationPackageId={
                  applicationPackage?.public_applicationPackage_id
                }
                applicationPackageTitle={
                  applicationPackage?.applicationPackage_title
                }
                openToApplicants={applicationPackage?.open_to_applicants}
              />
              <SubmissionWindow
                openingDate={applicationPackage?.opening_date}
                closingDate={applicationPackage?.closing_date}
                gracePeriod={applicationPackage?.grace_period}
              />
              <AgencyContact contactInfo={applicationPackage?.contact_info} />
              <ApplicationInstructions
                announcementId={announcementId}
                applicationPackageId={applicationPackageId}
                existingFiles={existingFiles}
              />
              <RequiredForms
                alwaysRequiredForms={alwaysRequiredForms}
                requiredForms={requiredForms}
                formDetails={forms}
              />
              <ModalToggleButton
                modalRef={formModalRef}
                opener
                className="usa-button usa-button--secondary"
                type="button"
              >
                {t("sectionRequiredForms.selectFormsButton")}
              </ModalToggleButton>
            </div>
            <div className="display-flex flex-justify margin-top-4">
              <div className="display-flex gap-2">
                <Button
                  type="submit"
                  data-submit-type="saveAndGoBack"
                  className="usa-button--outline"
                >
                  {isPending ? t("button.processing") : t("button.back")}
                </Button>
              </div>
              <FormSelectModal
                alwaysRequiredForms={alwaysRequiredForms}
                requiredForms={requiredForms}
                forms={forms}
                formModalRef={formModalRef}
                submitRequiredForms={(
                  forms: ApplicationPackageFormsSubmitApi,
                ) => {
                  setRequiredForms(forms);
                }}
              />
              <Button type="submit" data-submit-type="saveAndContinue">
                {isPending
                  ? t("button.processing")
                  : t("button.saveAndContinue")}
              </Button>
            </div>
          </section>
        </div>
      </div>
    </form>
  );
}

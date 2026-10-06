"use client";

import { LOGOUT_URL } from "src/constants/auth";

import { useTranslations } from "next-intl";
import { Alert, GridContainer } from "@trussworks/react-uswds";

export const SessionExpiredMessage = () => {
  const t = useTranslations("Errors");
  return (
    <GridContainer className="margin-top-4">
      <Alert type="info" heading={t("sessionExpiredHeading")} headingLevel="h4">
        {t("sessionExpiredBody")}
        <div className="margin-top-2">
          <a href={LOGOUT_URL} className="usa-button">
            {t("signInAgainCTA")}
          </a>
        </div>
      </Alert>
    </GridContainer>
  );
};

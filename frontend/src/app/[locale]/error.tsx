"use client";

import { parseErrorStatus } from "src/errors";

import { useTranslations } from "next-intl";
import { useEffect } from "react";
import { Button, GridContainer } from "@trussworks/react-uswds";

import GeneralErrorAlert from "src/components/core/GeneralErrorAlert";
import { SessionExpiredMessage } from "src/components/core/SessionExpiredMessage";

// Base error handling only
export default function RouteError({
  error,
  retry,
}: {
  error: Error & { digest?: string };
  retry: () => void;
}) {
  const t = useTranslations("Errors");

  useEffect(() => {
    console.error(error);
  }, [error]);

  if (parseErrorStatus(error) === 401) {
    return <SessionExpiredMessage />;
  }

  return (
    <GridContainer className="margin-top-4">
      <GeneralErrorAlert callToAction={t("tryAgain")} />
      <Button type="button" onClick={() => retry()} className="margin-top-2">
        {t("tryAgain")}
      </Button>
    </GridContainer>
  );
}

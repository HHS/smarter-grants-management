"use client";

import { publishFromOverview } from "src/app/[locale]/announcement/[id]/overview/actions";
import { getConfiguredDayJs } from "src/utils/dateUtil";

import { useTranslations } from "next-intl";
import { useState, useTransition } from "react";
import { Alert, Button } from "@trussworks/react-uswds";

type OverviewButtonsProps = {
  opportunityId: string;
  publishEnabled: boolean;
  postDate: string | null;
};

function isPastDate(value: string | null): boolean {
  if (!value) {
    return false;
  }
  const dayjs = getConfiguredDayJs();
  const date = dayjs(value, "YYYY-MM-DD", true);
  const today = dayjs().startOf("day");
  return date.isValid() && date.isBefore(today);
}

export function OverviewButtons({
  opportunityId,
  publishEnabled,
  postDate,
}: OverviewButtonsProps) {
  const t = useTranslations("AnnouncementOverview");
  const editT = useTranslations("OpportunityEdit");
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handlePublish = () => {
    setError(null);

    if (isPastDate(postDate)) {
      setError(editT("validationErrors.publishDatePast"));
      return;
    }

    startTransition(async () => {
      const result = await publishFromOverview(opportunityId);
      if (result?.errorMessage) {
        setError(result.errorMessage);
      }
    });
  };

  return (
    <>
      {error && (
        <Alert type="error" heading="Error" headingLevel="h4">
          {error}
        </Alert>
      )}
      <Button type="button" outline disabled>
        {t("labels.previewButton")}
      </Button>
      <Button
        type="button"
        disabled={!publishEnabled || isPending}
        onClick={handlePublish}
        className="margin-left-1"
      >
        {t("labels.publishButton")}
      </Button>
    </>
  );
}

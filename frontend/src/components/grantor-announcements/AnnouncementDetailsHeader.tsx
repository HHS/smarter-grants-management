import { timeZone } from "src/i18n/config";
import { GrantorAnnouncementDetail } from "src/types/announcement/announcementResponseTypes";

import { useTranslations } from "next-intl";
import { ReactNode } from "react";
import { Link } from "@trussworks/react-uswds";

import { USWDSIcon } from "src/components/core/USWDSIcon";

type OpportunityDetailsHeaderProps = {
  announcementData: GrantorAnnouncementDetail;
  locale: string;
  children?: ReactNode;
  hasBackToOverview?: boolean;
};

export function AnnouncementDetailsHeader({
  announcementData,
  locale,
  children,
  hasBackToOverview = false,
}: OpportunityDetailsHeaderProps) {
  const t = useTranslations("AnnouncementDetailsHeader");

  const opportunityId = announcementData.announcement_id;
  const opportunityNumber = announcementData.announcement_number ?? "";
  const title = announcementData.announcement_title ?? "";
  const agency = announcementData.top_level_agency_name ?? "";
  const subAgency = announcementData.agency_name ?? "";

  const rawLastUpdated = [
    announcementData.updated_at,
    announcementData.forecast_summary?.updated_at,
    announcementData.non_forecast_summary?.updated_at,
  ]
    .filter(Boolean)
    .sort()
    .at(-1);

  const lastUpdated = rawLastUpdated
    ? new Date(rawLastUpdated).toLocaleDateString(locale, {
        month: "2-digit",
        day: "2-digit",
        year: "numeric",
        timeZone,
      })
    : "";

  return (
    <section className="bg-base-lightest padding-y-6">
      <div className="grid-container">
        <div className="display-flex flex-justify">
          <div className="flex-1">
            {hasBackToOverview && (
              <Link href={"../" + opportunityId + "/overview"}>
                {t("backToOverview")}
              </Link>
            )}
            <h1 className="margin-0 font-heading-2xl margin-bottom-2">
              {t("opportunityNumber", { number: opportunityNumber })}
            </h1>
            <p className="margin-0 font-sans-md line-height-sans-5 margin-bottom-1">
              <span className="text-bold">{t("title")}</span> {title || "--"}
            </p>
            <p className="margin-0 font-sans-md line-height-sans-5 margin-bottom-2">
              <span className="text-bold">{t("agency")}</span> {agency || "--"}
              {subAgency ? (
                <>
                  {" | "}
                  <span className="text-bold">{t("subAgency")}</span>{" "}
                  {subAgency}
                </>
              ) : null}
            </p>
            <div className="display-flex flex-align-center gap-1">
              {announcementData.is_draft && (
                <span className="display-inline-flex flex-align-center bg-accent-warm text-ink padding-y-05 padding-x-1 radius-sm margin-right-1">
                  <USWDSIcon
                    name="schedule"
                    className="usa-icon width-2 height-2 margin-right-05"
                    aria-hidden="true"
                  />
                  {t("draft")}
                </span>
              )}
              {lastUpdated && (
                <span className="font-sans-md line-height-sans-5">
                  <span className="text-bold">{t("lastUpdated")}</span>{" "}
                  {lastUpdated}
                </span>
              )}
            </div>
          </div>
          {children && (
            <div className="display-flex flex-align-end gap-1">{children}</div>
          )}
        </div>
      </div>
    </section>
  );
}

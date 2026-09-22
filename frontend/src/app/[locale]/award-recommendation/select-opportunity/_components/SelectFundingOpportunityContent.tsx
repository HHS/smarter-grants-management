"use client";

import { createAwardRecommendationAction } from "src/app/[locale]/award-recommendation/select-opportunity/actions";
import { AnnouncementListItem } from "src/types/announcement/announcementResponseTypes";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@trussworks/react-uswds";

import {
  TableCellData,
  TableWithResponsiveHeader,
} from "src/components/core/TableWithResponsiveHeader";

type SelectFundingOpportunityContentProps = {
  announcements: AnnouncementListItem[];
};

export const SelectFundingOpportunityContent = ({
  announcements,
}: SelectFundingOpportunityContentProps) => {
  const t = useTranslations("AwardRecommendationSelectFundingOpportunity");
  const router = useRouter();
  const [creatingAnnouncementId, setCreatingAnnouncementId] = useState<
    string | null
  >(null);

  const handleCancel = () => {
    router.push("/");
  };

  const handleCreateAwardRecommendation = async (
    announcementId: string,
  ) => {
    setCreatingAnnouncementId(announcementId);

    try {
      const { awardRecommendationId } =
        await createAwardRecommendationAction(announcementId);

      router.push(`/award-recommendation/${awardRecommendationId}/edit`);
    } finally {
      setCreatingAnnouncementId(null);
    }
  };

  const headerContent: TableCellData[] = [
    { cellData: t("columns.fundingOpportunityNumber") },
    { cellData: t("columns.fundingOpportunityName") },
    { cellData: t("columns.submittedApplications") },
    { cellData: t("columns.action") },
  ];

  const tableRowData: TableCellData[][] = announcements.map((announcement) => {
    const isCreating = creatingAnnouncementId === announcement.announcement_id;

    return [
      {
        cellData: (
          <Link
            href={`/announcement/${announcement.announcement_id}`}
            className="usa-link"
          >
            {announcement.announcement_number}
          </Link>
        ),
      },
      { cellData: announcement.announcement_title },
      { cellData: 0 },
      {
        cellData: (
          <Button
            type="button"
            className="usa-button--outline margin-y-0"
            disabled={isCreating}
            onClick={() => {
              void handleCreateAwardRecommendation(announcement.announcement_id);
            }}
          >
            {t("startButtonText")} <span aria-hidden="true">→</span>
          </Button>
        ),
      },
    ];
  });

  return (
    <>
      <div className="margin-top-5 margin-bottom-5">
        <h2 className="margin-top-0 margin-bottom-2 font-sans-xl text-bold">
          {t("whichFundingOpportunity")}
        </h2>
      </div>

      <TableWithResponsiveHeader
        headerContent={headerContent}
        tableRowData={tableRowData}
      />

      <div className="margin-top-5">
        <Button
          type="button"
          className="usa-button--outline"
          onClick={handleCancel}
        >
          {t("cancelButtonText")}
        </Button>
      </div>
    </>
  );
};

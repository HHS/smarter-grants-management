import { Suspense } from "react";

import SummaryEditView from "src/components/announcement/SummaryEditView";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ id: string; summaryId: string }>;
};

export default async function AnnouncementSummaryEditPage({
  params,
}: PageProps) {
  const { id, summaryId } = await params;
  return <SummaryEditView announcementId={id} summaryId={summaryId} />;
}

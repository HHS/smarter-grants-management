import SummaryEditView from "src/components/announcement/SummaryEditView";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ id: string; type: string }>;
};

export default async function AnnouncementSummaryCreatePage({
  params,
}: PageProps) {
  const { id, type } = await params;

  return (
    <SummaryEditView
      announcementId={id}
      isForecast={type === "forecast"}
      createMode={true}
    />
  );
}

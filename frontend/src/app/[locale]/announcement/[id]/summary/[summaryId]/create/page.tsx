import SummaryEditView from "src/components/announcement/SummaryEditView";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ id: string; isForecast: string }>;
};

export default async function AnnouncementSummaryCreatePage({
  params,
}: PageProps) {
  const { id, isForecast } = await params;
  return (
    <SummaryEditView
      announcementId={id}
      isForecast={isForecast === "true"}
      createMode={true}
    />
  );
}

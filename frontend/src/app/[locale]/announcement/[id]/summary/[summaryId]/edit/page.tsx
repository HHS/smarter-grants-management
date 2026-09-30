import SummaryEditView from "src/components/announcement/SummaryEditView";

export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ id: string; locale: string }>;
};

export default async function AnnouncementEditPage({ params }: PageProps) {
  const { id } = await params;
  return <SummaryEditView announcementId={id} isForecast={false} />;
}

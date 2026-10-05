export const dynamic = "force-dynamic";

type PageProps = {
  params: Promise<{ id: string; locale: string }>;
};

// this needs to be changed from a summary edit page into an announcement edit page
export default async function AnnouncementEditPage({ params }: PageProps) {
  const { id } = await params;
  return <div>Edit the base announcement fields for {id}!!!</div>;
}

import { CreateAnnouncementForm } from "src/app/[locale]/announcements/create/_components/CreateAnnouncementForm";
import TopLevelError from "src/app/[locale]/error/page";
import { getSession } from "src/services/auth/session";

import { useTranslations } from "next-intl";
import { GridContainer } from "@trussworks/react-uswds";

import Breadcrumbs from "src/components/core/Breadcrumbs";

// Page Header component
const PageHeader = () => {
  const t = useTranslations("CreateOpportunity");
  return (
    <>
      <Breadcrumbs
        breadcrumbList={[
          { title: "home", path: "/" },
          {
            title: "Announcements",
            path: `/announcements`,
          },
          {
            title: "Create",
            path: `/announcements/create`,
          },
        ]}
      />

      <h1>{t("pageTitle")}</h1>
    </>
  );
};

// --- Main Page ---
export default async function CreateOpportunityPage() {
  const session = await getSession();
  if (!session?.token) {
    return <TopLevelError />;
  }

  return (
    <>
      <GridContainer>
        <PageHeader />
        <CreateAnnouncementForm />
      </GridContainer>
    </>
  );
}

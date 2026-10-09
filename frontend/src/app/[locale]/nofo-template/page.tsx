import { getTranslations } from "next-intl/server";
import Link from "next/link";
import { GridContainer } from "@trussworks/react-uswds";

export default async function NofoTemplateListPage() {
  const t = await getTranslations("NofoTemplate.List");
  return (
    <GridContainer>
      <h1 className="margin-top-9 margin-bottom-7">{t("pageTitle")}</h1>
      <Link href="/nofo-template/create" className="usa-button">
        Create NOFO Template
      </Link>
    </GridContainer>
  );
}

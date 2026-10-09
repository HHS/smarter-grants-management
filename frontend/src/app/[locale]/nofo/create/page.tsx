import { getTranslations } from "next-intl/server";
import { GridContainer } from "@trussworks/react-uswds";

export default async function NofoCreatePage() {
  const t = await getTranslations("Nofo.Create");
  return (
    <GridContainer>
      <h1 className="margin-top-9 margin-bottom-7">{t("pageTitle")}</h1>
    </GridContainer>
  );
}

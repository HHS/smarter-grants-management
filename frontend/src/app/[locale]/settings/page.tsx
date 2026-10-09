import { useTranslations } from "next-intl";
import { GridContainer } from "@trussworks/react-uswds";

export default function SettingsPage() {
  const t = useTranslations("Settings");

  return (
    <GridContainer>
      <h1 className="margin-top-9 margin-bottom-7">{t("heading")}</h1>
      <p>{t("body")}</p>
    </GridContainer>
  );
}

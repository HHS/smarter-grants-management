import { Metadata } from "next";
import { LayoutProps } from "src/types/generalTypes";
import { LocalizedPageProps } from "src/types/intl";

import { getTranslations } from "next-intl/server";

import { AuthenticationGate } from "src/components/core/AuthenticationGate";

export async function generateMetadata({ params }: LocalizedPageProps) {
  const { locale } = await params;
  const t = await getTranslations({ locale });
  const pageTitle =
    t("AnnouncementOverview.pageTitle") +
    " | " +
    t("AnnouncementOverview.pageApplication");
  const meta: Metadata = {
    title: pageTitle,
    description: t("AnnouncementOverview.metaDescription"),
  };
  return meta;
}

export default function UserLayout({ children }: LayoutProps) {
  return <AuthenticationGate>{children}</AuthenticationGate>;
}

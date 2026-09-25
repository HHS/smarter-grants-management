import { Metadata } from "next";
import { LayoutProps } from "src/types/generalTypes";

import { getTranslations } from "next-intl/server";

import { AuthenticationGate } from "src/components/core/AuthenticationGate";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string; locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({
    locale,
    namespace: "OpportunityApplicationPackage",
  });
  return {
    title: t("pageTitle"),
    description: t("metaDescription"),
  };
}

export default function ApplicationPackageLayout({ children }: LayoutProps) {
  return <AuthenticationGate>{children}</AuthenticationGate>;
}

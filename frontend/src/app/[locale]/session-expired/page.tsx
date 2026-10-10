import { Metadata } from "next";

import { getTranslations } from "next-intl/server";

import { SessionExpiredMessage } from "src/components/core/SessionExpiredMessage";

export async function generateMetadata() {
  const t = await getTranslations();
  const meta: Metadata = {
    title: t("ErrorPages.sessionExpired.pageTitle"),
    description: t("Homepage.metaDescription"),
  };
  return meta;
}

const SessionExpired = () => <SessionExpiredMessage />;

export default SessionExpired;

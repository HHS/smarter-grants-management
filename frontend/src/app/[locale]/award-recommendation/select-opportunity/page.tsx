import { Metadata } from "next";
import { SelectFundingOpportunityContent } from "src/app/[locale]/award-recommendation/select-opportunity/_components/SelectFundingOpportunityContent";
import withFeatureFlag from "src/services/featureFlags/withFeatureFlag";
import { searchAccessibleAnnouncements } from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import { WithFeatureFlagProps } from "src/types/uiTypes";

import { getTranslations } from "next-intl/server";
import { redirect } from "next/navigation";
import { GridContainer } from "@trussworks/react-uswds";

import CreateAwardRecommendationHeroContent from "src/components/award-recommendation/CreateAwardRecommendationHero";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const t = await getTranslations({ locale });
  const meta: Metadata = {
    title: t("AwardRecommendationSelectFundingOpportunity.pageTitle"),
    description: t(
      "AwardRecommendationSelectFundingOpportunity.metaDescription",
    ),
  };
  return meta;
}

const fetchFundingOpportunities = async () => {
  const json = await searchAccessibleAnnouncements({
    page_offset: 1,
    page_size: 25,
    sort_order: [
      {
        order_by: "created_at",
        sort_direction: "descending",
      },
    ],
  });

  return json.data;
};

export type SelectOpportunityPageProps = {
  params: Promise<{ locale: string }>;
} & WithFeatureFlagProps;

async function SelectOpportunityPageContent({
  params,
}: SelectOpportunityPageProps) {
  await params;
  const fundingOpportunities = await fetchFundingOpportunities();
  return (
    <>
      <CreateAwardRecommendationHeroContent />

      <GridContainer>
        <SelectFundingOpportunityContent
          announcements={fundingOpportunities}
        />
      </GridContainer>
    </>
  );
}

export default withFeatureFlag<SelectOpportunityPageProps, never>(
  SelectOpportunityPageContent,
  "awardRecommendationOff",
  () => redirect("/maintenance"),
);

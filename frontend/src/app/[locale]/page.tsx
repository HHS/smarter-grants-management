import { Metadata } from "next";
import { LocalizedPageProps } from "src/types/intl";

import { getTranslations } from "next-intl/server";
import { Grid, GridContainer } from "@trussworks/react-uswds";

export async function generateMetadata({
  params,
}: LocalizedPageProps): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale });
  const meta: Metadata = {
    title: t("Homepage.title"),
    description: t("Homepage.metaDescription"),
  };
  return meta;
}

export default function PlaceholderMgmtHomePage() {
  return (
    <div className="">
      <GridContainer className="display-flex flex-column padding-y-4 grid-container tablet-lg:flex-row tablet-lg:padding-y-6">
        <Grid row gap>
          <Grid tabletLg={{ col: 4 }}>
            <h2>Welcome to Smarter Grants Management</h2>
          </Grid>
          <Grid
            tabletLg={{ col: 8 }}
            className="margin-top-2 margin-bottom-0 tablet-lg:margin-0"
          >
            <a
              href="https://home.grantsolutions.gov/home/"
              target="_blank"
              rel="noopener noreferrer"
            >
              Visit Grant Solutions
            </a>
          </Grid>
        </Grid>
      </GridContainer>
    </div>
  );
}

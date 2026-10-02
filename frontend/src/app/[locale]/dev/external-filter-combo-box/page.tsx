import { Metadata } from "next";
import ExternalFilterComboBoxDemo from "src/app/[locale]/dev/external-filter-combo-box/_components/ExternalFilterComboBoxDemo";
import withFeatureFlag from "src/services/featureFlags/withFeatureFlag";
import { WithFeatureFlagProps } from "src/types/uiTypes";

import { notFound } from "next/navigation";

export function generateMetadata() {
  const meta: Metadata = {
    title: "External filter combo box",
  };

  return meta;
}

/**
 * Developer page for trying ExternalFilterComboBox against the real assistance listing search
 */
function ExternalFilterComboBoxPage() {
  return (
    <div className="grid-container">
      <h1>External filter combo box</h1>
      <ExternalFilterComboBoxDemo />
    </div>
  );
}

export default withFeatureFlag<WithFeatureFlagProps, never>(
  ExternalFilterComboBoxPage,
  "featureFlagAdminOff",
  () => notFound(),
);

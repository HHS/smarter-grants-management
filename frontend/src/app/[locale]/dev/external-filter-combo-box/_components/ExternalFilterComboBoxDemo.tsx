"use client";

import { AssistanceListing } from "src/types/assistanceListingTypes";

import { useState } from "react";
import { ComboBoxOption } from "@trussworks/react-uswds";

import { ExternalFilterComboBox } from "src/components/core/ExternalFilterComboBox";

const searchUrl = "/api/assistance-listings/search";
const description = "Search by assistance listing number or program title";

const formatAssistanceListingOptions = (response: unknown): ComboBoxOption[] =>
  (response as { data: AssistanceListing[] }).data.map((listing) => ({
    value: listing.assistance_listing_number,
    label: `${listing.assistance_listing_number} - ${listing.program_title}`,
  }));

const SelectionPayload = ({ selection }: { selection: ComboBoxOption[] }) => (
  <>
    <p className="text-bold">onSelectionChange payload</p>
    <pre className="bg-base-lightest padding-2">
      {JSON.stringify(selection, null, 2)}
    </pre>
  </>
);

/**
 * Single- and multi-select ExternalFilterComboBox, each showing the latest selection it reported
 */
export default function ExternalFilterComboBoxDemo() {
  const [singleSelection, setSingleSelection] = useState<ComboBoxOption[]>([]);
  const [multiSelection, setMultiSelection] = useState<ComboBoxOption[]>([]);

  return (
    <>
      <h2>Single select</h2>
      <ExternalFilterComboBox
        id="assistance-listing-single"
        name="assistance_listing_number"
        labelText="Assistance listing"
        description={description}
        placeholder="Search ALNs"
        fetchOptionsUrl={searchUrl}
        formatOptions={formatAssistanceListingOptions}
        onSelectionChange={setSingleSelection}
      />
      <SelectionPayload selection={singleSelection} />

      <h2>Multi-select</h2>
      <ExternalFilterComboBox
        id="assistance-listing-multi"
        name="assistance_listing_numbers"
        labelText="Assistance listings"
        description={description}
        placeholder="Search ALNs"
        fetchOptionsUrl={searchUrl}
        formatOptions={formatAssistanceListingOptions}
        multiSelect
        onSelectionChange={setMultiSelection}
      />
      <SelectionPayload selection={multiSelection} />
    </>
  );
}

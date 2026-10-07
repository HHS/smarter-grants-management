import { ComboBoxOption } from "@trussworks/react-uswds";

const externalFilterComboBoxSearchResponse = {
  data: [
    {
      assistance_listing_number: "10.001",
      program_title: "Agricultural Research",
    },
    { assistance_listing_number: "12.345", program_title: "Chemistry Program" },
    { assistance_listing_number: "66.111", program_title: "Chemical Safety" },
    {
      assistance_listing_number: "93.110",
      program_title: "Maternal and Child Health",
    },
  ],
};

const formatExternalFilterComboBoxOptions = (
  response: unknown,
): ComboBoxOption[] =>
  (response as typeof externalFilterComboBoxSearchResponse).data.map(
    (result) => ({
      value: result.assistance_listing_number,
      label: `${result.assistance_listing_number} - ${result.program_title}`,
    }),
  );

// sample data for the ExternalFilterComboBox tests and stories
export const fakeExternalFilterComboBox = {
  props: {
    id: "assistance-listing",
    name: "assistance_listing_numbers",
    labelText: "Assistance listing",
    description: "Search by assistance listing number or program title",
    placeholder: "Search ALNs",
    fetchOptionsUrl: "/api/assistance-listings/search",
    formatOptions: formatExternalFilterComboBoxOptions,
  },
  searchResponse: externalFilterComboBoxSearchResponse,
  options: formatExternalFilterComboBoxOptions(
    externalFilterComboBoxSearchResponse,
  ),
};

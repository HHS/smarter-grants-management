import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { ComboBoxOption } from "@trussworks/react-uswds";

import { ExternalFilterComboBox } from "src/components/core/ExternalFilterComboBox";

const mockSearchUrl = "/api/storybook/external-filter-combo-box";

// canned search response, returned for every search regardless of the text typed
const mockSearchResponse = {
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

type MockSearchResponse = typeof mockSearchResponse;

const formatMockOptions = (response: unknown): ComboBoxOption[] =>
  (response as MockSearchResponse).data.map((listing) => ({
    value: listing.assistance_listing_number,
    label: `${listing.assistance_listing_number} - ${listing.program_title}`,
  }));

const meta: Meta<typeof ExternalFilterComboBox> = {
  title: "Core Components/ExternalFilterComboBox",
  component: ExternalFilterComboBox,
  args: {
    id: "external-filter-combo-box",
    labelText: "Assistance listing",
    description: "Search by assistance listing number or program title",
    isRequired: false,
    rawErrors: [],
    disabled: false,
    minSearchLength: 3,
    debounceMs: 500,
    fetchOptionsUrl: mockSearchUrl,
    formatOptions: formatMockOptions,
  },
  argTypes: {
    id: {
      control: { type: "text" },
      description:
        "Id of the search input, also used to build label and error ids.",
      table: { type: { summary: "string" } },
    },
    labelText: {
      control: { type: "text" },
      description: "Visible field label.",
      table: { type: { summary: "string" } },
    },
    description: {
      control: { type: "text" },
      description: "Help text shown under the label.",
      table: { type: { summary: "string" } },
    },
    isRequired: {
      control: { type: "boolean" },
      description:
        "Shows the required asterisk. Does not add native validation.",
      table: { type: { summary: "boolean" } },
    },
    rawErrors: {
      control: { type: "object" },
      description: "Field errors shown above the input.",
      table: { type: { summary: "string[]" } },
    },
    disabled: {
      control: { type: "boolean" },
      description: "Disables the input.",
      table: { type: { summary: "boolean" } },
    },
    minSearchLength: {
      control: { type: "number", min: 1 },
      description:
        "Characters required before a search runs. Below this, the dropdown shows a hint.",
      table: { type: { summary: "number" }, defaultValue: { summary: "3" } },
    },
    debounceMs: {
      control: { type: "number", min: 0 },
      description:
        "Milliseconds typing must pause before a search request is sent.",
      table: { type: { summary: "number" }, defaultValue: { summary: "500" } },
    },
    fetchOptionsUrl: {
      control: false,
      description:
        "URL the search is POSTed to. In stories this is a mock URL answered by the withMockedClientFetch decorator.",
      table: { type: { summary: "string" } },
    },
    formatOptions: {
      control: false,
      description:
        "Turns the raw search response into the { value, label } options the dropdown shows.",
      table: { type: { summary: "(response: unknown) => ComboBoxOption[]" } },
    },
    buildRequestBody: {
      control: false,
      description: "Builds the POST body from the search text.",
      table: {
        type: { summary: "(searchTerm: string) => Record<string, unknown>" },
        defaultValue: { summary: "searchTerm => ({ searchTerm })" },
      },
    },
  },
  parameters: {
    // handled by the withMockedClientFetch decorator, no real API call is made
    mockFetch: {
      url: mockSearchUrl,
      responseBody: mockSearchResponse,
      delayMs: 300,
    },
  },
};
export default meta;

type Story = StoryObj<typeof ExternalFilterComboBox>;

export const Default: Story = {};

import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import { ExternalFilterComboBox } from "src/components/core/ExternalFilterComboBox";

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
  },
  parameters: {
    // handled by the withMockedClientFetch decorator, no real API call is made
    mockFetch: {
      url: "/api/storybook/external-filter-combo-box",
      responseBody: [],
    },
  },
};
export default meta;

type Story = StoryObj<typeof ExternalFilterComboBox>;

export const Default: Story = {};

import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fakeExternalFilterComboBox } from "src/utils/testing/fixtures";
import { action } from "storybook/actions";
import { expect, fn, userEvent, within } from "storybook/test";

import { FormEvent } from "react";
import { Button } from "@trussworks/react-uswds";

import { ExternalFilterComboBox } from "src/components/core/ExternalFilterComboBox";

// searchResponse is the canned response, returned for every search regardless of the text typed
const { props, searchResponse, options } = fakeExternalFilterComboBox;

const meta: Meta<typeof ExternalFilterComboBox> = {
  title: "Core Components/ExternalFilterComboBox",
  component: ExternalFilterComboBox,
  args: {
    ...props,
    isRequired: false,
    rawErrors: [],
    disabled: false,
    minSearchLength: 3,
    debounceMs: 500,
    multiSelect: false,
    defaultSelectedOptions: [],
    // logged in the Actions panel
    onSelectionChange: fn(),
  },
  argTypes: {
    id: {
      control: { type: "text" },
      description:
        "Id of the search input, also used to build label and error ids.",
      table: { type: { summary: "string" } },
    },
    name: {
      control: { type: "text" },
      description:
        "Form field name. Each selected value is submitted as name[0], name[1], ...",
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
    placeholder: {
      control: { type: "text" },
      description: "Hint text shown inside the empty input.",
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
    multiSelect: {
      control: { type: "boolean" },
      description:
        "Allows several selections, shown as removable pills below the input. Read on mount only, so remount the story after changing it.",
      table: {
        type: { summary: "boolean" },
        defaultValue: { summary: "false" },
      },
    },
    defaultSelectedOptions: {
      control: { type: "object" },
      description:
        "Options selected when the component mounts. Read on mount only, so remount the story after changing it.",
      table: {
        type: { summary: "ComboBoxOption[]" },
        defaultValue: { summary: "[]" },
      },
    },
    onSelectionChange: {
      control: false,
      description:
        "Called with the full list of selected options whenever the selection changes, and with an empty list when it is cleared.",
      table: {
        type: { summary: "(selectedOptions: ComboBoxOption[]) => void" },
      },
    },
  },
  parameters: {
    // handled by the withMockedClientFetch decorator, no real API call is made
    mockFetchConfiguration: {
      url: props.fetchOptionsUrl,
      responseBody: searchResponse,
      delayMs: 300,
    },
  },
};
export default meta;

type Story = StoryObj<typeof ExternalFilterComboBox>;

export const Default: Story = {};

export const DefaultSelection: Story = {
  args: {
    defaultSelectedOptions: [options[1]],
  },
};

export const MultiSelect: Story = {
  args: {
    multiSelect: true,
    defaultSelectedOptions: [options[3]],
  },
};

// the container is as wide as the input, so the pills wrap onto several lines
export const SeveralPills: Story = {
  args: {
    multiSelect: true,
    defaultSelectedOptions: options,
  },
  decorators: [
    (StoryComponent) => (
      <div className="maxw-mobile-lg">
        <StoryComponent />
      </div>
    ),
  ],
};

export const Disabled: Story = {
  args: {
    disabled: true,
    multiSelect: true,
    defaultSelectedOptions: [options[0]],
  },
};

export const RequiredWithError: Story = {
  args: {
    isRequired: true,
    rawErrors: ["This is a required field."],
  },
};

const logFormSubmission = action("form submitted");

// wraps the combo box in a form, and logs what the form would submit in the
// Actions panel instead of submitting it
const renderInForm: Story["render"] = (args) => (
  <form
    aria-label="Example form"
    onSubmit={(event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      logFormSubmission(Array.from(new FormData(event.currentTarget)));
    }}
  >
    <ExternalFilterComboBox {...args} />
    <Button type="submit" className="margin-top-2">
      Submit
    </Button>
  </form>
);

export const FormSubmission: Story = {
  render: renderInForm,
};

export const FormSubmissionMultiSelect: Story = {
  args: {
    multiSelect: true,
    defaultSelectedOptions: [options[3]],
  },
  render: renderInForm,
};

export const Loading: Story = {
  parameters: {
    mockFetchConfiguration: {
      url: props.fetchOptionsUrl,
      responseBody: searchResponse,
      delayMs: 5000,
    },
  },
};

// not exported as `Error`, which would shadow the global Error in this file
export const ErrorStory: Story = {
  name: "Error",
  parameters: {
    mockFetchConfiguration: {
      url: props.fetchOptionsUrl,
      responseBody: { message: "Internal server error" },
      status: 500,
    },
  },
};

// types a search when the story loads, so the dropdown opens with results
export const PopulatedResults: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await userEvent.type(canvas.getByRole("combobox"), "che");
    await expect(
      await canvas.findByRole(
        "option",
        { name: options[0].label },
        { timeout: 3000 },
      ),
    ).toBeVisible();
  },
};

export const NoResults: Story = {
  parameters: {
    mockFetchConfiguration: {
      url: props.fetchOptionsUrl,
      responseBody: { ...searchResponse, data: [] },
      delayMs: 300,
    },
  },
};

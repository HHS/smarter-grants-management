import { fireEvent, render, screen } from "@testing-library/react";
import { axe } from "jest-axe";
import ExternalFilterComboBoxPage from "src/app/[locale]/dev/external-filter-combo-box/page";

import { ComponentProps } from "react";

import { ExternalFilterComboBox } from "src/components/core/ExternalFilterComboBox";

type ComboBoxProps = ComponentProps<typeof ExternalFilterComboBox>;

const mockComboBoxProps = jest.fn();
const fakeSelection = [
  { value: "10.001", label: "10.001 - Agricultural Research" },
];

jest.mock("src/services/featureFlags/withFeatureFlag", () => ({
  __esModule: true,
  default: (WrappedComponent: React.FC) => WrappedComponent,
}));

jest.mock("src/components/core/ExternalFilterComboBox", () => ({
  ExternalFilterComboBox: (props: ComboBoxProps) => {
    mockComboBoxProps(props);
    return (
      <button
        type="button"
        onClick={() => props.onSelectionChange?.(fakeSelection)}
      >
        Select in {props.labelText}
      </button>
    );
  },
}));

// props from the latest render of the combo box with the given label
const propsFor = (labelText: string) =>
  mockComboBoxProps.mock.calls
    .map(([props]) => props as ComboBoxProps)
    .findLast((props) => props.labelText === labelText);

describe("External filter combo box dev page", () => {
  afterEach(() => jest.clearAllMocks());

  it("has no accessibility violations", async () => {
    const { container } = render(<ExternalFilterComboBoxPage />);

    const results = await axe(container);

    expect(results).toHaveNoViolations();
  });

  it("renders a single-select and a multi-select combo box against the search route", () => {
    render(<ExternalFilterComboBoxPage />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "External filter combo box",
      }),
    ).toBeInTheDocument();
    expect(propsFor("Assistance listing")).toMatchObject({
      fetchOptionsUrl: "/api/assistance-listings/search",
      placeholder: "Search ALNs",
    });
    expect(propsFor("Assistance listing")?.multiSelect).toBeUndefined();
    expect(propsFor("Assistance listings")).toMatchObject({
      fetchOptionsUrl: "/api/assistance-listings/search",
      placeholder: "Search ALNs",
      multiSelect: true,
    });
  });

  it("formats assistance listing search results as options", () => {
    render(<ExternalFilterComboBoxPage />);

    expect(
      propsFor("Assistance listing")?.formatOptions({
        data: [
          {
            assistance_listing_number: "10.001",
            program_title: "Agricultural Research",
          },
        ],
      }),
    ).toEqual(fakeSelection);
  });

  it("shows the latest selection reported by each combo box", () => {
    render(<ExternalFilterComboBoxPage />);
    expect(screen.getAllByText("[]")).toHaveLength(2);

    fireEvent.click(
      screen.getByRole("button", { name: "Select in Assistance listing" }),
    );

    expect(screen.getAllByText("[]")).toHaveLength(1);
    expect(screen.getByText(/"value": "10\.001"/)).toHaveTextContent(
      JSON.stringify(fakeSelection, null, 2),
      { normalizeWhitespace: false },
    );
  });
});

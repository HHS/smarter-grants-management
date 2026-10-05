import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { axe } from "jest-axe";
import { fakeExternalFilterComboBox } from "src/utils/testing/fixtures";

import { ComponentProps } from "react";
import { ComboBoxOption } from "@trussworks/react-uswds";

import { ExternalFilterComboBox } from "src/components/core/ExternalFilterComboBox";

const mockClientFetch = jest.fn();
let mockUserToken: string | undefined;

jest.mock("src/hooks/useClientFetch", () => ({
  useClientFetch: () => ({
    clientFetch: (...args: unknown[]) => mockClientFetch(...args) as unknown,
  }),
}));

jest.mock("src/services/auth/useUser", () => ({
  useUser: () => ({ user: { token: mockUserToken } }),
}));

const { props, searchResponse, options } = fakeExternalFilterComboBox;

const renderComboBox = (
  overrides: Partial<ComponentProps<typeof ExternalFilterComboBox>> = {},
) => render(<ExternalFilterComboBox {...props} {...overrides} />);

// the component's default debounceMs
const defaultDebounceMs = 500;

const typeInSearch = (text: string) =>
  fireEvent.change(screen.getByRole("combobox"), { target: { value: text } });

// runs the pending debounced search and lets its response settle
const waitForDebounce = (ms = defaultDebounceMs) =>
  act(async () => {
    jest.advanceTimersByTime(ms);
    await Promise.resolve();
  });

const focusSearch = () => act(() => screen.getByRole("combobox").focus());

const searchFor = async (text: string) => {
  focusSearch();
  typeInSearch(text);
  await waitForDebounce();
};

const pickOption = (option: ComboBoxOption) =>
  fireEvent.click(screen.getByRole("option", { name: option.label }));

const pillNames = () =>
  screen
    .queryAllByRole("button", { name: /^Remove .* pill$/ })
    .map((button) => button.getAttribute("aria-label"));

const renderInForm = (
  overrides: Partial<ComponentProps<typeof ExternalFilterComboBox>> = {},
) =>
  render(
    <form aria-label="Test form">
      <ExternalFilterComboBox {...props} {...overrides} />
    </form>,
  );

// every name/value pair the form would submit
const formEntries = () =>
  Array.from(
    new FormData(
      screen.getByRole<HTMLFormElement>("form", { name: "Test form" }),
    ),
  );

// text of every live status region, since trussworks renders its own as well
const statusMessages = () =>
  screen.getAllByRole("status").map((status) => status.textContent);

// a search response the test resolves when it chooses
const pendingResponse = () => {
  let resolveResponse: (response: unknown) => void = () => undefined;
  const promise = new Promise((resolve) => {
    resolveResponse = resolve;
  });
  return { promise, resolve: resolveResponse };
};

// rendering and props: accessibility, label, disabled, description, required marker,
// field errors, placeholder, and default selections in both modes
describe("ExternalFilterComboBox", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockUserToken = "a token";
    mockClientFetch.mockResolvedValue(searchResponse);
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.resetAllMocks();
  });

  it("has no accessibility violations", async () => {
    // axe schedules its own timers, which would never run under fake timers
    jest.useRealTimers();
    const { container } = renderComboBox();

    const results = await axe(container);

    expect(results).toHaveNoViolations();
  });

  it("renders the search input with its label", () => {
    renderComboBox();

    expect(
      screen.getByRole("combobox", { name: props.labelText }),
    ).toBeInTheDocument();
  });

  it("disables the search input", () => {
    renderComboBox({ disabled: true });

    expect(screen.getByRole("combobox")).toBeDisabled();
  });

  it("shows the description and the required marker", () => {
    renderComboBox({ isRequired: true });

    expect(screen.getByText(props.description)).toBeInTheDocument();
    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("shows field errors and links them to the input", () => {
    renderComboBox({ rawErrors: ["This is a required field."] });

    expect(screen.getByText("This is a required field.")).toBeInTheDocument();
    const input = screen.getByRole("combobox");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby", `error-for-${props.id}`);
  });

  it("does not mark the input invalid without errors", () => {
    renderComboBox();

    const input = screen.getByRole("combobox");
    expect(input).not.toHaveAttribute("aria-invalid");
    expect(input).not.toHaveAttribute("aria-describedby");
  });

  it("shows the placeholder in the empty input", () => {
    renderComboBox();

    expect(screen.getByRole("combobox")).toHaveAttribute(
      "placeholder",
      props.placeholder,
    );
  });

  it("shows a single-select default selection in the input", () => {
    renderComboBox({ defaultSelectedOptions: [options[0]] });

    expect(screen.getByRole("combobox")).toHaveValue(options[0].label);
    expect(pillNames()).toEqual([]);
  });

  it("shows multi-select default selections as pills", () => {
    renderComboBox({
      multiSelect: true,
      defaultSelectedOptions: options.slice(0, 2),
    });

    expect(screen.getByRole("combobox")).toHaveValue("");
    expect(pillNames()).toEqual([
      `Remove ${options[0].label} pill`,
      `Remove ${options[1].label} pill`,
    ]);
  });

  // when a search request is sent: minimum length hint, one request per typing pause,
  // default and custom request body, and waiting for the login token before searching
  describe("search", () => {
    it("shows the minimum length hint and does not search below the minimum", async () => {
      renderComboBox();

      typeInSearch("ch ");
      await waitForDebounce();

      expect(
        screen.getByText("Type at least 3 characters to search"),
      ).toBeVisible();
      expect(mockClientFetch).not.toHaveBeenCalled();
    });

    it("uses the singular hint for a minimum of one character", () => {
      renderComboBox({ minSearchLength: 1 });

      typeInSearch(" ");

      expect(
        screen.getByText("Type at least 1 character to search"),
      ).toBeVisible();
    });

    it("searches once, after typing pauses, with the default request body", async () => {
      renderComboBox();

      typeInSearch("c");
      typeInSearch("ch");
      typeInSearch("che");
      await waitForDebounce(defaultDebounceMs - 1);
      expect(mockClientFetch).not.toHaveBeenCalled();
      await waitForDebounce(1);

      expect(mockClientFetch).toHaveBeenCalledTimes(1);
      expect(mockClientFetch).toHaveBeenCalledWith(props.fetchOptionsUrl, {
        method: "POST",
        body: JSON.stringify({ searchTerm: "che" }),
      });
    });

    it("sends the request body built by buildRequestBody", async () => {
      renderComboBox({
        buildRequestBody: (searchTerm) => ({ query: searchTerm }),
      });

      typeInSearch("che");
      await waitForDebounce();

      expect(mockClientFetch).toHaveBeenCalledWith(props.fetchOptionsUrl, {
        method: "POST",
        body: JSON.stringify({ query: "che" }),
      });
    });

    it("does not search without a login token", async () => {
      mockUserToken = undefined;
      renderComboBox();

      typeInSearch("che");
      await waitForDebounce();

      expect(mockClientFetch).not.toHaveBeenCalled();
    });

    it("searches the typed text once the login token arrives", async () => {
      mockUserToken = undefined;
      const { rerender } = renderComboBox();
      typeInSearch("che");
      await waitForDebounce();
      expect(mockClientFetch).not.toHaveBeenCalled();

      // the session finishes loading
      mockUserToken = "a token";
      rerender(<ExternalFilterComboBox {...props} />);
      await waitForDebounce();

      expect(mockClientFetch).toHaveBeenCalledTimes(1);
      expect(mockClientFetch).toHaveBeenCalledWith(props.fetchOptionsUrl, {
        method: "POST",
        body: JSON.stringify({ searchTerm: "che" }),
      });
    });
  });

  // what the user sees before, while and after a search runs: results and their count, focus
  // kept, no results, loading spinner and message, error, out-of-order responses ignored
  describe("async states", () => {
    it("shows results as soon as they arrive and announces how many", async () => {
      renderComboBox();
      focusSearch();

      typeInSearch("che");
      await waitForDebounce();

      expect(
        screen.getAllByRole("option").map((option) => option.textContent),
      ).toEqual(options.map((option) => option.label));
      expect(statusMessages()).toContain(`${options.length} results available`);
    });

    it("does not pull focus back to the input when results arrive", async () => {
      render(
        <>
          <ExternalFilterComboBox {...props} />
          <button type="button">Next field</button>
        </>,
      );
      focusSearch();
      typeInSearch("che");
      const nextField = screen.getByRole("button", { name: "Next field" });

      act(() => nextField.focus());
      await waitForDebounce();

      expect(mockClientFetch).toHaveBeenCalledTimes(1);
      expect(nextField).toHaveFocus();
    });

    it("shows the no results message for an empty response", async () => {
      mockClientFetch.mockResolvedValue({ ...searchResponse, data: [] });
      renderComboBox();
      focusSearch();

      typeInSearch("zzz");
      await waitForDebounce();

      expect(
        within(screen.getByRole("listbox")).getByText("No results found"),
      ).toBeVisible();
      expect(statusMessages()).toContain("No results found");
    });

    it("shows a spinner while the search is loading, then removes it", async () => {
      const response = pendingResponse();
      mockClientFetch.mockReturnValue(response.promise);
      renderComboBox();
      focusSearch();

      typeInSearch("che");
      await waitForDebounce();

      expect(
        screen.getByRole("progressbar", { name: "Loading!" }),
      ).toBeInTheDocument();
      expect(
        within(screen.getByRole("listbox")).getByText("Loading results..."),
      ).toBeVisible();
      expect(statusMessages()).toContain("Loading results...");

      await act(async () => {
        response.resolve(searchResponse);
        await Promise.resolve();
      });

      expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    });

    it("shows loading, not no results, while waiting for typing to pause", () => {
      renderComboBox();
      focusSearch();

      typeInSearch("che");

      expect(mockClientFetch).not.toHaveBeenCalled();
      expect(
        within(screen.getByRole("listbox")).getByText("Loading results..."),
      ).toBeVisible();
    });

    it("shows the error message and drops earlier results when a search fails", async () => {
      const consoleError = jest
        .spyOn(console, "error")
        .mockImplementation(() => undefined);
      renderComboBox();
      focusSearch();
      typeInSearch("che");
      await waitForDebounce();
      expect(screen.getAllByRole("option")).toHaveLength(options.length);

      mockClientFetch.mockRejectedValue(new Error("search failed"));
      typeInSearch("chem");
      await waitForDebounce();

      expect(screen.queryAllByRole("option")).toHaveLength(0);
      expect(
        within(screen.getByRole("listbox")).getByText(
          "Unable to load results. Try again.",
        ),
      ).toBeVisible();
      expect(statusMessages()).toContain("Unable to load results. Try again.");
      expect(consoleError).toHaveBeenCalledWith(
        "Unable to fetch combo box options",
        new Error("search failed"),
      );
      consoleError.mockRestore();
    });

    it("ignores a response for text the user has since changed", async () => {
      const firstResponse = pendingResponse();
      const secondResponse = pendingResponse();
      mockClientFetch
        .mockReturnValueOnce(firstResponse.promise)
        .mockReturnValueOnce(secondResponse.promise);
      renderComboBox();
      focusSearch();
      typeInSearch("che");
      await waitForDebounce();
      typeInSearch("chem");
      await waitForDebounce();

      await act(async () => {
        secondResponse.resolve({
          ...searchResponse,
          data: searchResponse.data.slice(0, 1),
        });
        await Promise.resolve();
      });
      await act(async () => {
        firstResponse.resolve(searchResponse);
        await Promise.resolve();
      });

      expect(mockClientFetch).toHaveBeenCalledTimes(2);
      expect(
        screen.getAllByRole("option").map((option) => option.textContent),
      ).toEqual([options[0].label]);
    });
  });

  // onSelectionChange in single-select: nothing on mount, pick, replace, and clear,
  // each checked against the full list of calls
  describe("single-select", () => {
    it("does not report a selection on mount", () => {
      const onSelectionChange = jest.fn();
      const { unmount } = renderComboBox({ onSelectionChange });
      unmount();
      renderComboBox({
        onSelectionChange,
        defaultSelectedOptions: [options[0]],
      });

      expect(onSelectionChange).not.toHaveBeenCalled();
    });

    it("reports the picked option and shows it in the input", async () => {
      const onSelectionChange = jest.fn();
      renderComboBox({ onSelectionChange });

      await searchFor("che");
      pickOption(options[1]);

      expect(onSelectionChange.mock.calls).toEqual([[[options[1]]]]);
      expect(screen.getByRole("combobox")).toHaveValue(options[1].label);
    });

    it("replaces the selection when a different option is picked", async () => {
      const onSelectionChange = jest.fn();
      renderComboBox({ onSelectionChange });

      await searchFor("che");
      pickOption(options[1]);
      await searchFor("chem");
      pickOption(options[2]);

      expect(onSelectionChange.mock.calls).toEqual([
        [[options[1]]],
        [[options[2]]],
      ]);
      expect(screen.getByRole("combobox")).toHaveValue(options[2].label);
    });

    it("reports an empty selection when cleared", async () => {
      const onSelectionChange = jest.fn();
      renderComboBox({ onSelectionChange });

      await searchFor("che");
      pickOption(options[1]);
      fireEvent.click(
        screen.getByRole("button", { name: "Clear the select contents" }),
      );

      expect(onSelectionChange.mock.calls).toEqual([[[options[1]]], [[]]]);
      expect(screen.getByRole("combobox")).toHaveValue("");
    });
  });

  // pills in multi-select: adding, hiding picked options, no new results, removing one,
  // input cleared and refocused after a pick, no removal while disabled
  describe("multi-select", () => {
    it("adds a pill for each picked option and reports the full selection", async () => {
      const onSelectionChange = jest.fn();
      renderComboBox({ multiSelect: true, onSelectionChange });

      await searchFor("che");
      pickOption(options[0]);
      await searchFor("che");
      pickOption(options[2]);

      expect(onSelectionChange.mock.calls).toEqual([
        [[options[0]]],
        [[options[0], options[2]]],
      ]);
      expect(pillNames()).toEqual([
        `Remove ${options[0].label} pill`,
        `Remove ${options[2].label} pill`,
      ]);
    });

    it("does not offer options that are already picked", async () => {
      renderComboBox({
        multiSelect: true,
        defaultSelectedOptions: [options[0]],
      });

      await searchFor("che");

      expect(
        screen.getAllByRole("option").map((option) => option.textContent),
      ).toEqual(options.slice(1).map((option) => option.label));
    });

    it("shows no new results when every result is already picked", async () => {
      renderComboBox({ multiSelect: true, defaultSelectedOptions: options });

      await searchFor("che");

      expect(
        within(screen.getByRole("listbox")).getByText("No new results"),
      ).toBeVisible();
      expect(statusMessages()).toContain("No new results");
    });

    it("removes only the pill whose remove button is clicked", () => {
      const onSelectionChange = jest.fn();
      renderComboBox({
        multiSelect: true,
        defaultSelectedOptions: options.slice(0, 3),
        onSelectionChange,
      });

      fireEvent.click(
        screen.getByRole("button", { name: `Remove ${options[1].label} pill` }),
      );

      expect(onSelectionChange.mock.calls).toEqual([
        [[options[0], options[2]]],
      ]);
      expect(pillNames()).toEqual([
        `Remove ${options[0].label} pill`,
        `Remove ${options[2].label} pill`,
      ]);
    });

    it("clears the input and moves focus back to it after a pick", async () => {
      renderComboBox({ multiSelect: true });
      await searchFor("che");
      const option = screen.getByRole("option", { name: options[0].label });

      // a real mouse pick moves focus onto the option first
      act(() => option.focus());
      expect(option).toHaveFocus();
      fireEvent.click(option);

      const input = screen.getByRole("combobox");
      expect(input).toHaveValue("");
      expect(input).toHaveFocus();
    });

    it("does not remove a pill while disabled", () => {
      const onSelectionChange = jest.fn();
      renderComboBox({
        multiSelect: true,
        disabled: true,
        defaultSelectedOptions: [options[0]],
        onSelectionChange,
      });
      const removeButton = screen.getByRole("button", {
        name: `Remove ${options[0].label} pill`,
      });

      expect(removeButton).toBeDisabled();
      fireEvent.click(removeButton);

      expect(onSelectionChange).not.toHaveBeenCalled();
      expect(pillNames()).toEqual([`Remove ${options[0].label} pill`]);
    });
  });

  // what a wrapping form submits: one name[i] entry per selected value in both modes,
  // and nothing from the trussworks select or the search input
  describe("form submission", () => {
    it("submits the picked option in single-select", async () => {
      renderInForm();

      await searchFor("che");
      pickOption(options[1]);

      expect(formEntries()).toEqual([[`${props.name}[0]`, options[1].value]]);
    });

    it("submits only the latest pick in single-select", async () => {
      renderInForm();

      await searchFor("che");
      pickOption(options[1]);
      await searchFor("chem");
      pickOption(options[2]);

      expect(formEntries()).toEqual([[`${props.name}[0]`, options[2].value]]);
    });

    it("submits every pick in multi-select", async () => {
      renderInForm({ multiSelect: true, defaultSelectedOptions: [options[0]] });

      await searchFor("che");
      pickOption(options[2]);

      expect(formEntries()).toEqual([
        [`${props.name}[0]`, options[0].value],
        [`${props.name}[1]`, options[2].value],
      ]);
    });

    it("renumbers the submitted entries after a pill is removed", () => {
      renderInForm({
        multiSelect: true,
        defaultSelectedOptions: options.slice(0, 3),
      });

      fireEvent.click(
        screen.getByRole("button", { name: `Remove ${options[0].label} pill` }),
      );

      expect(formEntries()).toEqual([
        [`${props.name}[0]`, options[1].value],
        [`${props.name}[1]`, options[2].value],
      ]);
    });
  });

  // axe in the states the closed-field check above does not cover: the open dropdown
  // with results, several pills, and a field error (axe needs real timers)
  describe("accessibility", () => {
    it("has no violations with the dropdown open", async () => {
      const { container } = renderComboBox();
      await searchFor("che");
      expect(screen.getByRole("listbox")).toBeVisible();
      jest.useRealTimers();

      const results = await axe(container);

      expect(results).toHaveNoViolations();
    });

    it("has no violations with several pills", async () => {
      jest.useRealTimers();
      const { container } = renderComboBox({
        multiSelect: true,
        defaultSelectedOptions: options.slice(0, 2),
      });

      const results = await axe(container);

      expect(results).toHaveNoViolations();
    });

    it("has no violations with a field error", async () => {
      jest.useRealTimers();
      const { container } = renderComboBox({
        isRequired: true,
        rawErrors: ["This is a required field."],
      });

      const results = await axe(container);

      expect(results).toHaveNoViolations();
    });
  });
});

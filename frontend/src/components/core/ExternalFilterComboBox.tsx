"use client";

import { debounce } from "lodash";
import { useClientFetch } from "src/hooks/useClientFetch";
import { useUser } from "src/services/auth/useUser";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ComboBox,
  ComboBoxOption,
  ComboBoxRef,
  FormGroup,
} from "@trussworks/react-uswds";

import { DynamicFieldLabel } from "src/components/core/forms/DynamicFieldLabel";
import { FieldErrors } from "src/components/core/forms/FieldErrors";
import { Pill } from "src/components/core/Pill";
import Spinner from "src/components/core/Spinner";

type ExternalFilterComboBoxProps = {
  id: string;
  name: string;
  labelText: string;
  fetchOptionsUrl: string;
  formatOptions: (response: unknown) => ComboBoxOption[];
  buildRequestBody?: (searchTerm: string) => Record<string, unknown>;
  description?: string;
  placeholder?: string;
  isRequired?: boolean;
  rawErrors?: string[];
  disabled?: boolean;
  minSearchLength?: number;
  debounceMs?: number;
  multiSelect?: boolean;
  defaultSelectedOptions?: ComboBoxOption[];
  onSelectionChange?: (selectedOptions: ComboBoxOption[]) => void;
};

type SearchStatus = "idle" | "loading" | "success" | "error";

const defaultBuildRequestBody = (searchTerm: string) => ({ searchTerm });

const minimumLengthHint = (minSearchLength: number) =>
  `Type at least ${minSearchLength} character${minSearchLength === 1 ? "" : "s"} to search`;
const loadingMessage = "Loading results...";
const errorMessage = "Unable to load results. Try again.";
const noResultsMessage = "No results found";
const noNewResultsMessage = "No new results";

const resultCountMessage = (count: number) =>
  `${count} result${count === 1 ? "" : "s"} available`;

/**
 * Combo box whose options come from an API request made as the user types,
 * rather than from filtering a static list.
 */
export function ExternalFilterComboBox({
  id,
  name,
  labelText,
  fetchOptionsUrl,
  formatOptions,
  buildRequestBody = defaultBuildRequestBody,
  description,
  placeholder,
  isRequired = false,
  rawErrors = [],
  disabled = false,
  minSearchLength = 3,
  debounceMs = 500,
  multiSelect = false,
  defaultSelectedOptions = [],
  onSelectionChange,
}: ExternalFilterComboBoxProps) {
  const hasErrors = rawErrors.length > 0;
  const [searchTerm, setSearchTerm] = useState("");
  // trussworks only shows a default value that is among the options present on mount,
  // and search results have not arrived yet then, so a single-select default starts
  // as the options. Multi-select defaults show as pills instead.
  const [options, setOptions] = useState<ComboBoxOption[]>(
    multiSelect ? [] : defaultSelectedOptions,
  );
  const [selectedOptions, setSelectedOptions] = useState<ComboBoxOption[]>(
    defaultSelectedOptions,
  );
  const [searchStatus, setSearchStatus] = useState<SearchStatus>("idle");
  const isBelowMinimumLength = searchTerm.length < minSearchLength;

  // multi-select does not offer options that are already selected
  const availableOptions = multiSelect
    ? options.filter(
        (option) =>
          !selectedOptions.some((selected) => selected.value === option.value),
      )
    : options;
  const hasOnlySelectedResults =
    options.length > 0 && availableOptions.length === 0;

  const comboBoxRef = useRef<ComboBoxRef>(null);
  // identifies the most recent search, so responses that arrive after the user has
  // typed again (or after a newer search started) are ignored
  const latestRequestId = useRef(0);
  const pillsRef = useRef<HTMLDivElement>(null);
  // position of a pill just removed, so focus can move to the pill now in its place
  const removedPillIndex = useRef<number | null>(null);
  const { user } = useUser();
  const hasToken = Boolean(user?.token);
  const { clientFetch } = useClientFetch<unknown>(
    "Error fetching combo box options",
  );

  // the text to search for, set once typing pauses for debounceMs. A new object each
  // time, so a pause on the same text as the last search still searches again (that
  // search's response is ignored once the text changed in between).
  const [debouncedSearch, setDebouncedSearch] = useState({ term: "" });
  const updateDebouncedSearch = useMemo(
    () => debounce((term: string) => setDebouncedSearch({ term }), debounceMs),
    [debounceMs],
  );
  useEffect(
    () => () => updateDebouncedSearch.cancel(),
    [updateDebouncedSearch],
  );

  // searches for the debounced text. Text typed before the session loads is searched
  // as soon as the token arrives.
  useEffect(() => {
    const term = debouncedSearch.term;
    if (term.length < minSearchLength || !hasToken) return;
    latestRequestId.current += 1;
    const requestId = latestRequestId.current;
    const searchAbortController = new AbortController();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSearchStatus("loading");
    clientFetch(fetchOptionsUrl, {
      method: "POST",
      body: JSON.stringify(buildRequestBody(term)),
      signal: searchAbortController.signal,
    })
      .then((response) => {
        if (requestId === latestRequestId.current) {
          setOptions(formatOptions(response));
          setSearchStatus("success");
        }
        return null;
      })
      .catch((e: Error) => {
        // skip handling for expected abort related errors
        if (e.name === "AbortError" || requestId !== latestRequestId.current) {
          return;
        }
        console.error("Unable to fetch combo box options", e);
        setOptions([]);
        setSearchStatus("error");
      });
    // a newer search, or the component going away, cancels this request
    return () => searchAbortController.abort();
    // only a new debounced search or the token arriving starts a search. clientFetch
    // as a dependency causes an infinite re-render loop (see the note in
    // useClientFetch), and the props are read when the search starts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch, hasToken]);

  // trussworks ComboBox copies new options into its state without re-rendering
  // (https://github.com/trussworks/react-uswds/issues/3592), so results would not
  // show until the next keystroke. focus() dispatches a real state update, which
  // re-renders with the new options. Only done while the input already has focus,
  // so it never pulls focus back from somewhere else.
  useEffect(() => {
    if (document.activeElement?.id === id) {
      comboBoxRef.current?.focus();
    }
  }, [options, id]);

  // the remove button of a removed pill disappears, so keyboard focus moves to the
  // pill now in its place, the previous pill if it was the last, or the search input
  useEffect(() => {
    const index = removedPillIndex.current;
    if (index === null) return;
    removedPillIndex.current = null;
    const removeButtons = pillsRef.current?.querySelectorAll("button") ?? [];
    const nextButton =
      removeButtons[Math.min(index, removeButtons.length - 1)] ?? null;
    if (nextButton) {
      nextButton.focus();
    } else {
      comboBoxRef.current?.focus();
    }
  }, [selectedOptions]);

  // trussworks ComboBox overwrites any aria-describedby passed through inputProps
  // (https://github.com/trussworks/react-uswds/issues/3449), so it is set on the
  // rendered input directly
  useEffect(() => {
    const input = document.getElementById(id);
    if (!input) return;
    if (hasErrors) {
      input.setAttribute("aria-describedby", `error-for-${id}`);
    } else {
      input.removeAttribute("aria-describedby");
    }
  }, [id, hasErrors]);

  const onInputChange = (value: string) => {
    const term = value.trim();
    setSearchTerm(term);
    updateDebouncedSearch(term);
    // any response still on its way is for text the user has since changed
    latestRequestId.current += 1;
    // results for a longer search no longer apply once the text drops below the minimum
    if (term.length < minSearchLength) {
      setOptions([]);
      setSearchStatus("idle");
    }
  };

  const updateSelection = (newSelection: ComboBoxOption[]) => {
    setSelectedOptions(newSelection);
    onSelectionChange?.(newSelection);
  };

  // trussworks reports the selected value whenever its selection changes, including
  // on mount and undefined on clear, so only an actual change is passed on
  const onComboBoxChange = (value?: string) => {
    if (multiSelect) {
      // undefined here comes from mount or from the clearSelection() below
      if (!value) return;
      const addedOption = availableOptions.find(
        (option) => option.value === value,
      );
      if (!addedOption) return;
      updateSelection([...selectedOptions, addedOption]);
      // empty the input, ready for the next search
      comboBoxRef.current?.clearSelection();
      comboBoxRef.current?.focus();
      onInputChange("");
      return;
    }
    if (value === selectedOptions[0]?.value) return;
    const selectedOption = options.find((option) => option.value === value);
    if (value && !selectedOption) return;
    updateSelection(selectedOption ? [selectedOption] : []);
  };

  const removeOption = (value: string) => {
    removedPillIndex.current = selectedOptions.findIndex(
      (selected) => selected.value === value,
    );
    updateSelection(
      selectedOptions.filter((selected) => selected.value !== value),
    );
  };

  // the only text trussworks can show inside the dropdown, shown when there are no options
  const dropdownMessage = isBelowMinimumLength
    ? minimumLengthHint(minSearchLength)
    : searchStatus === "error"
      ? errorMessage
      : searchStatus === "success"
        ? hasOnlySelectedResults
          ? noNewResultsMessage
          : noResultsMessage
        : // the search is waiting for typing to pause, or still loading
          loadingMessage;

  // trussworks' own screen reader status is computed before async results arrive,
  // so the search state is announced here instead
  const statusAnnouncement =
    isBelowMinimumLength || searchStatus === "idle"
      ? ""
      : searchStatus === "loading"
        ? loadingMessage
        : searchStatus === "error"
          ? errorMessage
          : availableOptions.length
            ? resultCountMessage(availableOptions.length)
            : hasOnlySelectedResults
              ? noNewResultsMessage
              : noResultsMessage;

  return (
    <FormGroup error={hasErrors || undefined}>
      <DynamicFieldLabel
        idFor={id}
        title={labelText}
        required={isRequired}
        description={description}
      />
      {hasErrors ? <FieldErrors fieldName={id} rawErrors={rawErrors} /> : null}
      {/* the selection is submitted as an array, one hidden input per selected value */}
      {selectedOptions.map((option, index) => (
        <input
          key={option.value}
          type="hidden"
          name={`${name}[${index}]`}
          value={option.value}
        />
      ))}
      <div className="display-flex flex-align-center">
        <ComboBox
          ref={comboBoxRef}
          className="width-full"
          id={id}
          // selections are submitted through the hidden inputs above, since the hidden
          // select trussworks renders does not track the selected value
          // (https://github.com/trussworks/react-uswds/issues/3591)
          name=""
          options={availableOptions}
          defaultValue={
            multiSelect ? undefined : defaultSelectedOptions[0]?.value
          }
          onChange={onComboBoxChange}
          disabled={disabled}
          inputProps={{
            "aria-invalid": hasErrors || undefined,
            placeholder,
            // trussworks onChange only fires on selection, so keystrokes are read here
            onChange: (e) => onInputChange(e.target.value),
          }}
          noResults={dropdownMessage}
          // options come pre-filtered from the API
          disableFiltering
          // gives the dropdown list an accessible name
          ulProps={{ "aria-labelledby": `label-for-${id}` }}
        />
        {searchStatus === "loading" ? (
          <Spinner className="height-3 width-3 margin-left-1" />
        ) : null}
      </div>
      {multiSelect && selectedOptions.length > 0 ? (
        <div ref={pillsRef} className="margin-top-1 display-flex flex-wrap">
          {selectedOptions.map((option) => (
            <div key={option.value} className="margin-right-1 margin-bottom-1">
              <Pill
                label={option.label}
                onClose={() => removeOption(option.value)}
                disabled={disabled}
              />
            </div>
          ))}
        </div>
      ) : null}
      <div role="status" className="usa-sr-only">
        {statusAnnouncement}
      </div>
    </FormGroup>
  );
}

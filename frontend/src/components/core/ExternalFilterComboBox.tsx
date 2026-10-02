"use client";

import { useClientFetch } from "src/hooks/useClientFetch";
import { useUser } from "src/services/auth/useUser";

import { useEffect, useEffectEvent, useRef, useState } from "react";
import {
  ComboBox,
  ComboBoxOption,
  ComboBoxRef,
  FormGroup,
} from "@trussworks/react-uswds";

import { DynamicFieldLabel } from "src/components/core/forms/DynamicFieldLabel";
import { FieldErrors } from "src/components/core/forms/FieldErrors";
import Spinner from "src/components/core/Spinner";

type ExternalFilterComboBoxProps = {
  id: string;
  labelText: string;
  fetchOptionsUrl: string;
  formatOptions: (response: unknown) => ComboBoxOption[];
  buildRequestBody?: (searchTerm: string) => Record<string, unknown>;
  description?: string;
  isRequired?: boolean;
  rawErrors?: string[];
  disabled?: boolean;
  minSearchLength?: number;
  debounceMs?: number;
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

const resultCountMessage = (count: number) =>
  `${count} result${count === 1 ? "" : "s"} available`;

/**
 * Combo box whose options come from an API request made as the user types,
 * rather than from filtering a static list.
 */
export function ExternalFilterComboBox({
  id,
  labelText,
  fetchOptionsUrl,
  formatOptions,
  buildRequestBody = defaultBuildRequestBody,
  description,
  isRequired = false,
  rawErrors = [],
  disabled = false,
  minSearchLength = 3,
  debounceMs = 500,
  defaultSelectedOptions = [],
  onSelectionChange,
}: ExternalFilterComboBoxProps) {
  const hasErrors = rawErrors.length > 0;
  const [inputValue, setInputValue] = useState("");
  // trussworks only shows a default value that is among the options present on mount,
  // and search results have not arrived yet then, so the defaults start as the options
  const [options, setOptions] = useState<ComboBoxOption[]>(
    defaultSelectedOptions,
  );
  const [selectedOptions, setSelectedOptions] = useState<ComboBoxOption[]>(
    defaultSelectedOptions,
  );
  const [searchStatus, setSearchStatus] = useState<SearchStatus>("idle");
  const searchTerm = inputValue.trim();
  const isBelowMinimumLength = searchTerm.length < minSearchLength;

  const comboBoxRef = useRef<ComboBoxRef>(null);
  // identifies the most recent search, so responses that arrive after the user has
  // typed again (or after a newer search started) are ignored
  const latestRequestId = useRef(0);
  const { user } = useUser();
  const { clientFetch } = useClientFetch<unknown>(
    "Error fetching combo box options",
  );

  // an effect event always sees the latest props and clientFetch without them being
  // effect dependencies (clientFetch as a dependency causes an infinite re-render
  // loop, see the note in useClientFetch)
  const search = useEffectEvent((term: string) => {
    if (!user?.token) return;
    latestRequestId.current += 1;
    const requestId = latestRequestId.current;
    setSearchStatus("loading");
    clientFetch(fetchOptionsUrl, {
      method: "POST",
      body: JSON.stringify(buildRequestBody(term)),
    })
      .then((response) => {
        if (requestId === latestRequestId.current) {
          setOptions(formatOptions(response));
          setSearchStatus("success");
        }
        return null;
      })
      .catch((e) => {
        if (requestId !== latestRequestId.current) return;
        console.error("Unable to fetch combo box options", e);
        setOptions([]);
        setSearchStatus("error");
      });
  });

  // searches once typing pauses for debounceMs; the cleanup cancels the pending
  // search on every keystroke and when the component unmounts
  useEffect(() => {
    if (isBelowMinimumLength) return;
    const timer = setTimeout(() => search(searchTerm), debounceMs);
    return () => clearTimeout(timer);
  }, [searchTerm, isBelowMinimumLength, debounceMs]);

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
    setInputValue(value);
    // any response still on its way is for text the user has since changed
    latestRequestId.current += 1;
    // results for a longer search no longer apply once the text drops below the minimum
    if (value.trim().length < minSearchLength) {
      setOptions([]);
      setSearchStatus("idle");
    }
  };

  // trussworks reports the selected value whenever its selection changes, including
  // on mount and undefined on clear, so only an actual change is passed on
  const onComboBoxChange = (value?: string) => {
    if (value === selectedOptions[0]?.value) return;
    const selectedOption = options.find((option) => option.value === value);
    if (value && !selectedOption) return;
    const newSelection = selectedOption ? [selectedOption] : [];
    setSelectedOptions(newSelection);
    onSelectionChange?.(newSelection);
  };

  // the only text trussworks can show inside the dropdown, shown when there are no options
  const dropdownMessage = isBelowMinimumLength
    ? minimumLengthHint(minSearchLength)
    : searchStatus === "loading"
      ? loadingMessage
      : searchStatus === "error"
        ? errorMessage
        : noResultsMessage;

  // trussworks' own screen reader status is computed before async results arrive,
  // so the search state is announced here instead
  const statusAnnouncement =
    isBelowMinimumLength || searchStatus === "idle"
      ? ""
      : searchStatus === "loading"
        ? loadingMessage
        : searchStatus === "error"
          ? errorMessage
          : options.length
            ? resultCountMessage(options.length)
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
      <div className="display-flex flex-align-center">
        <ComboBox
          ref={comboBoxRef}
          className="width-full"
          id={id}
          // selections are submitted through hidden inputs, since the hidden select
          // trussworks renders does not track the selected value
          // (https://github.com/trussworks/react-uswds/issues/3591)
          name=""
          options={options}
          defaultValue={defaultSelectedOptions[0]?.value}
          onChange={onComboBoxChange}
          disabled={disabled}
          inputProps={{
            "aria-invalid": hasErrors || undefined,
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
      <div role="status" className="usa-sr-only">
        {statusAnnouncement}
      </div>
    </FormGroup>
  );
}

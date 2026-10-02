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
};

const defaultBuildRequestBody = (searchTerm: string) => ({ searchTerm });

const minimumLengthHint = (minSearchLength: number) =>
  `Type at least ${minSearchLength} character${minSearchLength === 1 ? "" : "s"} to search`;

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
}: ExternalFilterComboBoxProps) {
  const hasErrors = rawErrors.length > 0;
  const [inputValue, setInputValue] = useState("");
  const [options, setOptions] = useState<ComboBoxOption[]>([]);
  const searchTerm = inputValue.trim();
  const isBelowMinimumLength = searchTerm.length < minSearchLength;

  const comboBoxRef = useRef<ComboBoxRef>(null);
  const { user } = useUser();
  const { clientFetch } = useClientFetch<unknown>(
    "Error fetching combo box options",
  );

  // an effect event always sees the latest props and clientFetch without them being
  // effect dependencies (clientFetch as a dependency causes an infinite re-render
  // loop, see the note in useClientFetch)
  const search = useEffectEvent((term: string) => {
    if (!user?.token) return;
    clientFetch(fetchOptionsUrl, {
      method: "POST",
      body: JSON.stringify(buildRequestBody(term)),
    })
      .then((response) => setOptions(formatOptions(response)))
      .catch((e) => {
        console.error("Unable to fetch combo box options", e);
        setOptions([]);
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
    // results for a longer search no longer apply once the text drops below the minimum
    if (value.trim().length < minSearchLength) {
      setOptions([]);
    }
  };

  return (
    <FormGroup error={hasErrors || undefined}>
      <DynamicFieldLabel
        idFor={id}
        title={labelText}
        required={isRequired}
        description={description}
      />
      {hasErrors ? <FieldErrors fieldName={id} rawErrors={rawErrors} /> : null}
      <ComboBox
        ref={comboBoxRef}
        id={id}
        // selections are submitted through hidden inputs, since the hidden select
        // trussworks renders does not track the selected value
        // (https://github.com/trussworks/react-uswds/issues/3591)
        name=""
        options={options}
        onChange={() => undefined}
        disabled={disabled}
        inputProps={{
          "aria-invalid": hasErrors || undefined,
          // trussworks onChange only fires on selection, so keystrokes are read here
          onChange: (e) => onInputChange(e.target.value),
        }}
        // the only text trussworks can show inside the dropdown
        noResults={
          isBelowMinimumLength ? minimumLengthHint(minSearchLength) : undefined
        }
        // options come pre-filtered from the API
        disableFiltering
        // gives the dropdown list an accessible name
        ulProps={{ "aria-labelledby": `label-for-${id}` }}
      />
    </FormGroup>
  );
}

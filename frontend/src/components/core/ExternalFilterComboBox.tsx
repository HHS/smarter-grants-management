"use client";

import { useEffect } from "react";
import { ComboBox, FormGroup } from "@trussworks/react-uswds";

import { DynamicFieldLabel } from "src/components/core/forms/DynamicFieldLabel";
import { FieldErrors } from "src/components/core/forms/FieldErrors";

type ExternalFilterComboBoxProps = {
  id: string;
  labelText: string;
  description?: string;
  isRequired?: boolean;
  rawErrors?: string[];
  disabled?: boolean;
};

/**
 * Combo box whose options come from an API request made as the user types,
 * rather than from filtering a static list.
 */
export function ExternalFilterComboBox({
  id,
  labelText,
  description,
  isRequired = false,
  rawErrors = [],
  disabled = false,
}: ExternalFilterComboBoxProps) {
  const hasErrors = rawErrors.length > 0;

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
        id={id}
        // selections are submitted through hidden inputs, since the hidden select
        // trussworks renders does not track the selected value
        // (https://github.com/trussworks/react-uswds/issues/3591)
        name=""
        options={[]}
        onChange={() => undefined}
        disabled={disabled}
        inputProps={{ "aria-invalid": hasErrors || undefined }}
        // options come pre-filtered from the API
        disableFiltering
        // gives the dropdown list an accessible name
        ulProps={{ "aria-labelledby": `label-for-${id}` }}
      />
    </FormGroup>
  );
}

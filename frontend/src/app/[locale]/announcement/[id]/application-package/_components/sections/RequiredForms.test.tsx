import { render, screen } from "@testing-library/react";
import { axe } from "jest-axe";
import { RequiredForms } from "src/app/[locale]/announcement/[id]/application-package/_components/sections/RequiredForms";
import { FormType } from "src/types/allFormsResponseTypes";

jest.mock("next-intl", () => ({
  useTranslations: jest.fn(() => (key: string) => key),
}));

const alwaysRequiredForms: Record<string, boolean> = {
  "111": true,
};

describe("RequiredForms", () => {
  const alwaysRequiredFormId = 111;
  const conditionalFormId = 222;

  const mockFormDetails: FormType[] = [
    {
      form_id: alwaysRequiredFormId,
      short_name: "SF424_V1",
      name: "Application for Federal Assistance (SF-424)",
      version: "1.0",
    },
    {
      form_id: conditionalFormId,
      short_name: "CD511_V2",
      name: "Certification Form (CD-511)",
      version: "2.1",
    },
  ];

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("required form status", () => {
    it("renders required status when is_required is true", () => {
      render(
        <RequiredForms
          alwaysRequiredForms={alwaysRequiredForms}
          requiredForms={[
            {
              form_id: alwaysRequiredFormId,
              is_required: true,
            },
          ]}
          formDetails={mockFormDetails}
        />,
      );

      expect(screen.getByText("requiredStates.required")).toBeInTheDocument();
    });

    it("renders conditional status when is_required is false", () => {
      render(
        <RequiredForms
          alwaysRequiredForms={alwaysRequiredForms}
          requiredForms={[
            {
              form_id: conditionalFormId,
              is_required: false,
            },
          ]}
          formDetails={mockFormDetails}
        />,
      );

      expect(
        screen.getByText("requiredStates.conditional"),
      ).toBeInTheDocument();
    });
  });

  describe("always required forms", () => {
    it("renders the always label for forms in the always required list", () => {
      render(
        <RequiredForms
          alwaysRequiredForms={alwaysRequiredForms}
          requiredForms={[
            {
              form_id: alwaysRequiredFormId,
              is_required: true,
            },
          ]}
          formDetails={mockFormDetails}
        />,
      );

      expect(screen.getByText("requiredStates.always")).toBeInTheDocument();
    });

    it("renders no requirements when requiredForms is empty", () => {
      render(
        <RequiredForms
          alwaysRequiredForms={alwaysRequiredForms}
          requiredForms={[]}
          formDetails={mockFormDetails}
        />,
      );

      expect(
        screen.queryByText("requiredStates.always"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText("requiredStates.required"),
      ).not.toBeInTheDocument();
      expect(
        screen.queryByText("requiredStates.conditional"),
      ).not.toBeInTheDocument();
    });
  });

  describe("form details", () => {
    it("renders the form short name and version", () => {
      render(
        <RequiredForms
          alwaysRequiredForms={alwaysRequiredForms}
          requiredForms={[
            {
              form_id: alwaysRequiredFormId,
              is_required: true,
            },
          ]}
          formDetails={mockFormDetails}
        />,
      );

      expect(screen.getByText("SF424")).toBeInTheDocument();
      expect(screen.getByText("v1.0")).toBeInTheDocument();
    });

    it("renders form name without the parenthetical suffix", () => {
      render(
        <RequiredForms
          alwaysRequiredForms={alwaysRequiredForms}
          requiredForms={[
            {
              form_id: alwaysRequiredFormId,
              is_required: true,
            },
          ]}
          formDetails={mockFormDetails}
        />,
      );

      expect(
        screen.getByText("Application for Federal Assistance"),
      ).toBeInTheDocument();
    });

    it("does not render a requirement label when matching form details are not found", () => {
      render(
        <RequiredForms
          alwaysRequiredForms={alwaysRequiredForms}
          requiredForms={[
            {
              form_id: 999,
              is_required: true,
            },
          ]}
          formDetails={[]}
        />,
      );

      expect(
        screen.queryByText("requiredStates.required"),
      ).not.toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("passes accessibility scan when rendering a required form", async () => {
      const { container } = render(
        <RequiredForms
          alwaysRequiredForms={alwaysRequiredForms}
          requiredForms={[
            {
              form_id: alwaysRequiredFormId,
              is_required: true,
            },
          ]}
          formDetails={mockFormDetails}
        />,
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("passes accessibility scan when rendering a conditional form", async () => {
      const { container } = render(
        <RequiredForms
          alwaysRequiredForms={alwaysRequiredForms}
          requiredForms={[
            {
              form_id: conditionalFormId,
              is_required: false,
            },
          ]}
          formDetails={mockFormDetails}
        />,
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { noop } from "lodash";
import { CreateAnnouncementForm } from "src/app/[locale]/announcements/create/_components/CreateAnnouncementForm";

const mockUseActionState = jest.fn();

jest.mock("react", () => ({
  ...jest.requireActual<typeof import("react")>("react"),
  useActionState: () => mockUseActionState() as unknown,
}));

jest.mock("src/app/[locale]/announcements/create/actions", () => ({
  createOpportunityAction: noop,
}));

jest.mock("next/navigation", () => ({
  useRouter: jest.fn().mockReturnValue({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
    pathname: "/",
    query: {},
    asPath: "/",
  }),
  usePathname: jest.fn(() => "/"),
  useSearchParams: jest.fn(() => new URLSearchParams()),
}));

describe("createOpportunityForm", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  // --- Test the return values from action ---
  it("displays values from form action when available", () => {
    mockUseActionState.mockReturnValue([
      {
        data: {
          announcement_id: "opp-001",
          announcement_number: "MY-TEST-001",
          announcement_title: "Test Opportunity 001",
          category: "other",
          category_explanation: "",
          assistance_listing_number: "12.345",
        },
      },
      noop,
      false,
    ]);

    render(<CreateAnnouncementForm />);

    expect(screen.getByDisplayValue("MY-TEST-001")).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("Test Opportunity 001"),
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("12.345")).toBeInTheDocument();
  });

  // --- Test errors from action ---
  it("displays error message on error", () => {
    mockUseActionState.mockReturnValue([
      { errorMessage: "big error" },
      noop,
      false,
    ]);

    render(<CreateAnnouncementForm />);

    const alert = screen.getByRole("heading", { name: "errorHeading" });
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveTextContent("errorHeading");

    const errorText = screen.getByText("big error");
    expect(errorText).toBeInTheDocument();
  });
});

describe("createOpportunityForm field change events", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("the save button is enabled when required fields have values", async () => {
    mockUseActionState.mockReturnValue([{}, noop, false]);

    render(<CreateAnnouncementForm />);

    // 1. Initially the save button is disabled
    const saveButton = screen.queryByText("saveAndContinue");
    expect(saveButton).toBeInTheDocument();
    expect(saveButton).toBeDisabled();

    // 2. Fill in Opportunity Number
    const textboxOppNbr = screen.getByRole("textbox", {
      name: "CreateAnnouncementForm.opportunityNumber *",
    });
    expect(textboxOppNbr).toBeInTheDocument();
    expect(textboxOppNbr).toHaveValue("");
    fireEvent.change(textboxOppNbr, { target: { value: "TEST-001" } });
    expect(textboxOppNbr).toHaveValue("TEST-001");
    // Save button should still be disabled
    expect(saveButton).toBeDisabled();

    // 3. Fill in Opportunity Title
    const textareaOppTitle = screen.getByRole("textbox", {
      name: "CreateAnnouncementForm.opportunityTitle *",
    });
    expect(textareaOppTitle).toBeInTheDocument();
    expect(textareaOppTitle).toHaveValue("");
    fireEvent.change(textareaOppTitle, {
      target: { value: "Test Opportunity 001" },
    });
    expect(textareaOppTitle).toHaveValue("Test Opportunity 001");
    // Save button should still be disabled
    expect(saveButton).toBeDisabled();

    // 4. Fill in Opportunity Title
    const textboxTagLine = screen.getByRole("textbox", {
      name: "CreateAnnouncementForm.tagline *",
    });
    expect(textboxTagLine).toBeInTheDocument();
    expect(textboxTagLine).toHaveValue("");
    fireEvent.change(textboxTagLine, {
      target: { value: "Funding tagline" },
    });
    expect(textboxTagLine).toHaveValue("Funding tagline");
    // Save button should still be disabled
    expect(saveButton).toBeDisabled();

    // 5. Fill in Opportunity Title
    const textboxPurpose = screen.getByRole("textbox", {
      name: "CreateAnnouncementForm.purposeStatement *",
    });
    expect(textboxPurpose).toBeInTheDocument();
    expect(textboxPurpose).toHaveValue("");
    fireEvent.change(textboxPurpose, {
      target: { value: "Funding purpose statement" },
    });
    expect(textboxPurpose).toHaveValue("Funding purpose statement");
    // Save button should still be disabled
    expect(saveButton).toBeDisabled();

    // 6. Enter an ALN
    const assitListNbr = screen.getByRole("textbox", {
      name: "CreateAnnouncementForm.assistanceListingNumber *",
    });
    expect(assitListNbr).toBeInTheDocument();
    expect(assitListNbr).toHaveValue("");
    fireEvent.change(assitListNbr, { target: { value: "12.345" } });
    expect(assitListNbr).toHaveValue("12.345");
    // Save button should still be disabled
    expect(saveButton).toBeDisabled();

    // 7. Select a Category that is not "other"
    const selectCategory = screen.getByRole("combobox", {
      name: "CreateAnnouncementForm.category *",
    });
    expect(selectCategory).toBeInTheDocument();
    expect(selectCategory).toHaveValue("");
    await userEvent.selectOptions(selectCategory, "discretionary");
    expect(selectCategory).toHaveValue("discretionary");
    // Save button should now be enabled
    expect(saveButton).toBeEnabled();
    // The Explanation field should be hidden
    const testExplain = screen.queryByRole("textbox", {
      name: "CreateAnnouncementForm.categoryExplanation *",
    });
    expect(testExplain).not.toBeInTheDocument();

    // 8. Select "other" for the Category
    await userEvent.selectOptions(selectCategory, "other");
    expect(selectCategory).toHaveValue("other");
    // Save button should now be disabled
    expect(saveButton).toBeDisabled();
    // The Explanation field should now be displayed
    const textareaExplain = screen.getByRole("textbox", {
      name: "CreateAnnouncementForm.categoryExplanation *",
    });
    expect(textareaExplain).toBeInTheDocument();
    expect(textareaExplain).toHaveValue("");

    // 9. Fill in the Category Explanation field
    fireEvent.change(textareaExplain, {
      target: { value: "Sample Explanation" },
    });
    expect(textareaExplain).toHaveValue("Sample Explanation");
    // Save button should now be enabled
    expect(saveButton).toBeEnabled();

    // 10. Remove/delete the text in Opportunity Title
    fireEvent.change(textareaOppTitle, {
      target: { value: "" },
    });
    expect(textareaOppTitle).toHaveValue("");
    // Save button should be disabled again
    expect(saveButton).toBeDisabled();
  });
});

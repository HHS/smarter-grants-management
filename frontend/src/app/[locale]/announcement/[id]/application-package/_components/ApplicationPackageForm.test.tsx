import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  fakeApplicationPackageWithOpportunity,
  fakeFormType,
} from "src/utils/testing/fixtures";

import { ApplicationPackageForm } from "./ApplicationPackageForm";

const mockApplicationPackageAction = jest.fn();
const mockScrollTo = jest.fn();
const mockClientFetch = jest.fn();

jest.mock(
  "src/app/[locale]/announcement/[id]/application-package/actions",
  () => ({
    applicationPackageFormAction: (formData: unknown) =>
      mockApplicationPackageAction(formData) as unknown,
  }),
);

jest.mock("src/hooks/useClientFetch", () => ({
  useClientFetch: jest.fn(() => ({
    clientFetch: mockClientFetch,
  })),
}));
let originalScrollTo: typeof global.window.scrollTo;

describe("ApplicationPackage", () => {
  beforeEach(() => {
    // the bind here is to work around a linting issue, shouldn't effect behavior at all
    originalScrollTo = global.window.scrollTo.bind(global.window);
    global.window.scrollTo = mockScrollTo;
  });
  afterEach(() => {
    global.window.scrollTo = originalScrollTo;
    jest.resetAllMocks();
  });
  it("scrolls to the top on validation errors", async () => {
    mockApplicationPackageAction.mockResolvedValue({
      validationErrors: ["an error string"],
    });
    render(
      <ApplicationPackageForm
        announcementId="1"
        applicationPackage={fakeApplicationPackageWithOpportunity}
        forms={[fakeFormType]}
      />,
    );
    const submitButton = screen.getByRole("button", {
      name: "button.saveAndContinue",
    });
    await userEvent.click(submitButton);
    expect(mockApplicationPackageAction).toHaveBeenCalledTimes(1);
    expect(mockScrollTo).toHaveBeenCalledTimes(1);
  });
});

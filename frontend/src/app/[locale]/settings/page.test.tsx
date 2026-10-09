import { render, screen } from "@testing-library/react";
import { axe } from "jest-axe";
import SettingsPage from "src/app/[locale]/settings/page";
import { useTranslationsMock } from "src/utils/testing/intlMocks";

jest.mock("next-intl", () => ({
  useTranslations: () => useTranslationsMock(),
}));

describe("SettingsPage", () => {
  it("renders the settings heading", () => {
    render(<SettingsPage />);

    expect(
      screen.getByRole("heading", { name: "heading" }),
    ).toBeInTheDocument();
  });

  it("passes accessibility scan", async () => {
    const { container } = render(<SettingsPage />);
    const results = await axe(container);

    expect(results).toHaveNoViolations();
  });
});

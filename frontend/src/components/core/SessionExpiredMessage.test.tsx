import { render, screen } from "@testing-library/react";
import { axe } from "jest-axe";

import { SessionExpiredMessage } from "src/components/core/SessionExpiredMessage";

describe("SessionExpiredMessage", () => {
  it("should display the session expired message and a sign in link", () => {
    render(<SessionExpiredMessage />);
    expect(screen.getByText("sessionExpiredHeading")).toBeInTheDocument();
    expect(screen.getByText("sessionExpiredBody")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "signInAgainCTA" }),
    ).toHaveAttribute("href", "/api/auth/login");
  });

  it("should not have any accessibility violations", async () => {
    const { container } = render(<SessionExpiredMessage />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

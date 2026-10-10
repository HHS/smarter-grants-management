import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { UnauthorizedError } from "src/errors";

import RouteError from "./error";

describe("RouteError", () => {
  it("renders the session expired message for a 401 error", () => {
    const error = new UnauthorizedError("session expired or invalid");
    render(<RouteError error={error} retry={jest.fn()} />);
    expect(screen.getByText("sessionExpiredHeading")).toBeInTheDocument();
  });
  it("renders a generic error alert with a retry button for other errors", async () => {
    const retry = jest.fn();
    render(<RouteError error={new Error("boom")} retry={retry} />);
    expect(screen.getByText("heading")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "tryAgain" }));
    expect(retry).toHaveBeenCalledTimes(1);
  });
});

import { render, screen } from "@testing-library/react";
import { useTranslationsMock } from "src/utils/testing/intlMocks";

import AnnouncementStatusTag from "./AnnouncementStatusTag";

jest.mock("next-intl", () => ({
  useTranslations: () => useTranslationsMock(),
}));

describe("AnnouncementStatusTag", () => {
  it("renders draft status with icon", () => {
    render(<AnnouncementStatusTag status="draft" />);
    expect(screen.getByTestId("opportunity-status-draft")).toBeInTheDocument();
    expect(screen.getByText("draft")).toBeInTheDocument();
  });

  it("renders posted status", () => {
    render(<AnnouncementStatusTag status="posted" />);
    expect(screen.getByTestId("announcement-status-posted")).toBeInTheDocument();
    expect(screen.getByText("posted")).toBeInTheDocument();
  });

  it("renders forecasted status", () => {
    render(<AnnouncementStatusTag status="forecasted" />);
    expect(
      screen.getByTestId("announcement-status-forecasted"),
    ).toBeInTheDocument();
    expect(screen.getByText("forecasted")).toBeInTheDocument();
  });

  it("renders archived status", () => {
    render(<AnnouncementStatusTag status="archived" />);
    expect(
      screen.getByTestId("opportunity-status-archived"),
    ).toBeInTheDocument();
    expect(screen.getByText("archived")).toBeInTheDocument();
  });

  it("renders closed status", () => {
    render(<AnnouncementStatusTag status="closed" />);
    expect(screen.getByTestId("opportunity-status-closed")).toBeInTheDocument();
    expect(screen.getByText("closed")).toBeInTheDocument();
  });
});

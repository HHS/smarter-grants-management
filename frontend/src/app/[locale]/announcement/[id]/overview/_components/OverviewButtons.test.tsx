import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import dayjs from "dayjs";
import { publishFromOverview } from "src/app/[locale]/announcement/[id]/overview/actions";

import { OverviewButtons } from "./OverviewButtons";

jest.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}));

jest.mock("src/app/[locale]/announcement/[id]/overview/actions", () => ({
  publishFromOverview: jest.fn(),
}));

const mockPublishFromOverview = jest.mocked(publishFromOverview);

const today = dayjs().startOf("day");
const pastDate = today.subtract(1, "day").format("YYYY-MM-DD");
const futureDate = today.add(1, "day").format("YYYY-MM-DD");

describe("OverviewButtons", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("shows an error and does not publish when postDate is in the past", async () => {
    const user = userEvent.setup();
    render(
      <OverviewButtons
        opportunityId="opp-123"
        publishEnabled={true}
        postDate={pastDate}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "labels.publishButton" }),
    );

    expect(
      screen.getByText("validationErrors.publishDatePast"),
    ).toBeInTheDocument();
    expect(mockPublishFromOverview).not.toHaveBeenCalled();
  });

  it("publishes when postDate is today", async () => {
    const user = userEvent.setup();
    // publishFromOverview redirects on success (never resolves in real usage);
    // the unconfigured mock's default resolved value of `undefined` stands in.
    render(
      <OverviewButtons
        opportunityId="opp-123"
        publishEnabled={true}
        postDate={today.format("YYYY-MM-DD")}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "labels.publishButton" }),
    );

    expect(mockPublishFromOverview).toHaveBeenCalledWith("opp-123");
    expect(
      screen.queryByText("validationErrors.publishDatePast"),
    ).not.toBeInTheDocument();
  });

  it("publishes when postDate is in the future", async () => {
    const user = userEvent.setup();
    // publishFromOverview redirects on success (never resolves in real usage);
    // the unconfigured mock's default resolved value of `undefined` stands in.
    render(
      <OverviewButtons
        opportunityId="opp-123"
        publishEnabled={true}
        postDate={futureDate}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "labels.publishButton" }),
    );

    expect(mockPublishFromOverview).toHaveBeenCalledWith("opp-123");
  });

  it("shows the server error when publishFromOverview fails", async () => {
    const user = userEvent.setup();
    mockPublishFromOverview.mockResolvedValue({ errorMessage: "notFound" });
    render(
      <OverviewButtons
        opportunityId="opp-123"
        publishEnabled={true}
        postDate={futureDate}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "labels.publishButton" }),
    );

    expect(await screen.findByText("notFound")).toBeInTheDocument();
  });

  it("does not render the publish button as clickable when publishEnabled is false", () => {
    render(
      <OverviewButtons
        opportunityId="opp-123"
        publishEnabled={false}
        postDate={futureDate}
      />,
    );

    expect(
      screen.getByRole("button", { name: "labels.publishButton" }),
    ).toBeDisabled();
  });
});

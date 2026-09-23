import { summarizeNetworkEvents } from "tests/e2e/utils/common/failure-debug-artifacts-utils";

describe("failure debug artifacts utils", () => {
  it("summarizes request and response events in a readable format", () => {
    const entries = [
      "[request] GET /announcements",
      "[response] 200 /announcements",
      "[request] GET /api/opportunities",
      "[response] 500 /api/opportunities",
    ];

    expect(summarizeNetworkEvents(entries)).toContain("GET /announcements");
    expect(summarizeNetworkEvents(entries)).toContain("500 /api/opportunities");
  });
});

import { computeAnnouncementPublishEligibility } from "src/utils/announcement/announcementPublishEligibility";

import { progressType } from "src/components/grantor-announcements/ProgressChecker";

describe("computeAnnouncementPublishEligibility", () => {
  it("is eligible when a draft and both sections are complete", () => {
    expect(
      computeAnnouncementPublishEligibility(
        true,
        progressType.complete,
        progressType.complete,
      ),
    ).toBe(true);
  });

  it("is not eligible when not a draft, even if both sections are complete", () => {
    expect(
      computeAnnouncementPublishEligibility(
        false,
        progressType.complete,
        progressType.complete,
      ),
    ).toBe(false);
  });

  it("is not eligible when one section is in progress, even if the other is complete", () => {
    expect(
      computeAnnouncementPublishEligibility(
        true,
        progressType.complete,
        progressType.inProgress,
      ),
    ).toBe(false);
  });

  it("is not eligible when both sections are not started", () => {
    expect(
      computeAnnouncementPublishEligibility(
        true,
        progressType.notStarted,
        progressType.notStarted,
      ),
    ).toBe(false);
  });
});

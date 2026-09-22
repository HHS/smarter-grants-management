import { progressType } from "src/components/grantor-announcements/ProgressChecker";

export function computeAnnouncementPublishEligibility(
  isDraft: boolean,
  summaryStatus: (typeof progressType)[keyof typeof progressType],
  competitionStatus: (typeof progressType)[keyof typeof progressType],
): boolean {
  return (
    isDraft &&
    (summaryStatus === progressType.complete ||
      competitionStatus === progressType.complete) &&
    summaryStatus !== progressType.inProgress &&
    competitionStatus !== progressType.inProgress
  );
}

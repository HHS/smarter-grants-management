// import { progressType } from "src/components/grantor-announcements/ProgressChecker";

// export function computeAnnouncementPublishEligibility(
//   isDraft: boolean,
//   summaryStatus: (typeof progressType)[keyof typeof progressType],
//   applicationPackageStatus: (typeof progressType)[keyof typeof progressType],
// ): boolean {
//   return (
//     isDraft &&
//     (summaryStatus === progressType.complete ||
//       applicationPackageStatus === progressType.complete) &&
//     summaryStatus !== progressType.inProgress &&
//     applicationPackageStatus !== progressType.inProgress
//   );
// }

// temporarily disable all publishing, this will be a more complex calculation based on announcement type
export const computeAnnouncementPublishEligibility = () => false;

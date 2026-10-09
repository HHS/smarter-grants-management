import { GrantorAnnouncementDetail } from "src/types/announcement/announcementResponseTypes";
import { timestampPassed } from "src/utils/dateUtil";

/*
  disable forecast forms if
    - non_forecast_summary exists
    - forecast_summary.forecasted_close_timestamp has passed
*/
export const shouldDisableForecast = (
  announcement: GrantorAnnouncementDetail,
): boolean => {
  if (
    announcement.non_forecast_summary &&
    announcement.forecast_summary?.forecasted_close_timestamp &&
    timestampPassed(announcement.forecast_summary?.forecasted_close_timestamp)
  ) {
    return true;
  }
  return false;
};

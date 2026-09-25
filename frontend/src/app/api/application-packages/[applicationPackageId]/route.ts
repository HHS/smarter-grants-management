import { respondWithTraceAndLogs } from "src/utils/apiUtils";

import { getApplicationPackage } from "./handler";

export const GET = respondWithTraceAndLogs<{ applicationPackageId: string }>(
  getApplicationPackage,
);

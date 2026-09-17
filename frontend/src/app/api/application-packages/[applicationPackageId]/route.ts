import { respondWithTraceAndLogs } from "src/utils/apiUtils";

import { getCompetition } from "./handler";

export const GET = respondWithTraceAndLogs<{ applicationPackageId: string }>(
  getCompetition,
);

import { respondWithTraceAndLogs } from "src/utils/apiUtils";

import { searchAssistanceListings } from "./handler";

export const POST = respondWithTraceAndLogs(searchAssistanceListings);

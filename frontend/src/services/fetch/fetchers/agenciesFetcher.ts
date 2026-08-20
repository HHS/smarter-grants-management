"server only";

import { fetchUserWithMethod } from "src/services/fetch/fetchers/fetchers";
import { RelevantAgencyRecord } from "src/types/search/searchFilterTypes";

// ------------------------------------------------------
// Fetch user's agencies
// ------------------------------------------------------
export const getUserAgencies = async (
  userId: string,
): Promise<RelevantAgencyRecord[]> => {
  const subPath = `${userId}/agencies`;
  const resp = await fetchUserWithMethod("POST")({
    subPath,
  });
  const json = (await resp.json()) as { data: [] };
  return json.data;
};

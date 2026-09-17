import "server-only";

import { ApplicationPackage } from "src/types/applicationpackageResponseTypes";

import { fetchCompetition } from "./fetchers";

export const getCompetitionDetails = async (
  id: string,
): Promise<ApplicationPackage> => {
  const response = await fetchCompetition({ subPath: id });
  const responseBody = (await response.json()) as { data: ApplicationPackage };

  return responseBody.data;
};

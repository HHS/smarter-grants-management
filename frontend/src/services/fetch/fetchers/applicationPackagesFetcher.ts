import "server-only";

import { ApplicationPackage } from "src/types/applicationPackageResponseTypes";

import { fetchApplicationPackage } from "./fetchers";

export const getApplicationPackageDetails = async (
  id: string,
): Promise<ApplicationPackage> => {
  const response = await fetchApplicationPackage({ subPath: id });
  const responseBody = (await response.json()) as { data: ApplicationPackage };

  return responseBody.data;
};

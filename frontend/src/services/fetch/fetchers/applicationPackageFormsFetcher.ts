import { ApplicationPackageFormsApiResponse } from "src/types/applicationPackageFormsResponseTypes";
import { ApplicationPackageFormsSubmitApi } from "src/types/applicationPackageResponseTypes";

import { fetchApplicationPackageForms } from "./fetchers";

export async function updateApplicationPackageForms({
  applicationPackageId,
  body,
}: {
  applicationPackageId: string;
  body: { forms: ApplicationPackageFormsSubmitApi };
}): Promise<ApplicationPackageFormsApiResponse> {
  const response = await fetchApplicationPackageForms({
    subPath: `${applicationPackageId}/forms`,
    body,
  });

  return (await response.json()) as ApplicationPackageFormsApiResponse;
}

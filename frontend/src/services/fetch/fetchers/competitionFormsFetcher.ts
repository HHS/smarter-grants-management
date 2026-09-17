import { ApplicationPackageFormsApiResponse } from "src/types/applicationpackageFormsResponseTypes";
import { ApplicationPackageFormsSubmitApi } from "src/types/applicationpackageResponseTypes";

import { fetchCompetitionForms } from "./fetchers";

export async function updateCompetitionForms({
  competitionId,
  body,
}: {
  competitionId: string;
  body: { forms: ApplicationPackageFormsSubmitApi };
}): Promise<ApplicationPackageFormsApiResponse> {
  const response = await fetchCompetitionForms({
    subPath: `${competitionId}/forms`,
    body,
  });

  return (await response.json()) as ApplicationPackageFormsApiResponse;
}

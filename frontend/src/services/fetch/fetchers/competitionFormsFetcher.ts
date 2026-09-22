import { ApplicationPackageFormsApiResponse } from "src/types/applicationPackageFormsResponseTypes";
import { ApplicationPackageFormsSubmitApi } from "src/types/applicationPackageResponseTypes";

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

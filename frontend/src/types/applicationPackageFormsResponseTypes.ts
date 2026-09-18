import { APIResponse } from "src/types/apiResponseTypes";

import { ApplicationPackage } from "./applicationPackageResponseTypes";

export interface ApplicationPackageFormsApiResponse extends APIResponse {
  data: ApplicationPackage;
}

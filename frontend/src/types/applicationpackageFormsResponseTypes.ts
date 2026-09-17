import { APIResponse } from "src/types/apiResponseTypes";

import { ApplicationPackage } from "./applicationpackageResponseTypes";

export interface ApplicationPackageFormsApiResponse extends APIResponse {
  data: ApplicationPackage;
}

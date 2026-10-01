import { APIResponse } from "src/types/apiResponseTypes";

export interface FormType {
  form_id: number;
  name: string;
  short_name: string;
  version: string;
}

export interface AllFormsApiResponse extends APIResponse {
  data: FormType[];
  message: string;
  status_code: number;
}

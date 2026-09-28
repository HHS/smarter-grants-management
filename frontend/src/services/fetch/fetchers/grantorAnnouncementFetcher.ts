"server-only";

import {
  fetchAnnouncementWithMethod,
  fetchGrantorAgenciesWithMethod,
} from "src/services/fetch/fetchers/fetchers";
import {
  AnnouncementSummaryCreateRequest,
  AnnouncementSummaryDetailApiResponse,
  AnnouncementSummaryUpdateRequest,
  GrantorAnnouncementApiResponse,
} from "src/types/announcement/announcementResponseTypes";
import { APIResponse, PaginationInfo } from "src/types/apiResponseTypes";
import { ApplicationPackageFormsApiResponse } from "src/types/applicationPackageFormsResponseTypes";
import {
  ApplicationPackageFormsSubmitApi,
  ApplicationPackageInstructionsApiResponse,
  ApplicationPackageSaveApiResponse,
  ApplicationPackageSaveRequest,
} from "src/types/applicationPackageResponseTypes";
import { CreateAnnouncementRecord } from "src/types/createAnnouncementTypes";
import {
  AnnouncementListAPIResponse,
  AnnouncementListResponseData,
  PaginationRequestBody,
  SearchAPIResponse,
  SearchResponseData,
} from "src/types/search/searchRequestTypes";

type PaginationBody = {
  pagination: PaginationRequestBody;
};

type UpdateAnnouncementSummaryParams = {
  announcementId: string;
  announcementSummaryId: string;
  body: AnnouncementSummaryUpdateRequest;
};

type CreateAnnouncementSummaryParams = {
  announcementId: string;
  body: AnnouncementSummaryCreateRequest;
};

type UpdateApplicationPackageFormsParams = {
  announcementId: string;
  applicationPackageId: string;
  body: { forms: ApplicationPackageFormsSubmitApi };
};

export const searchOpportunitiesByAgency = async (
  agencyId: string,
  pageInputs: PaginationRequestBody,
): Promise<{ data: SearchResponseData; pagination_info: PaginationInfo }> => {
  const pagination = pageInputs;
  const pageBody: PaginationBody = { pagination };

  const response = await fetchGrantorAgenciesWithMethod("POST")({
    subPath: `${agencyId}/announcements`,
    body: pageBody,
  });
  return (await response.json()) as SearchAPIResponse;
};

export const searchAccessibleAnnouncements = async (
  pageInputs: PaginationRequestBody,
): Promise<{
  data: AnnouncementListResponseData;
  pagination_info: PaginationInfo;
}> => {
  const response = await fetchAnnouncementWithMethod("POST")({
    subPath: "list",
    body: { pagination: pageInputs },
  });

  return (await response.json()) as AnnouncementListAPIResponse;
};

export async function getAnnouncement(
  opportunityId: string,
): Promise<GrantorAnnouncementApiResponse> {
  const response = await fetchAnnouncementWithMethod("GET")({
    subPath: opportunityId,
  });
  return (await response.json()) as GrantorAnnouncementApiResponse;
}

export const createOpportunity = async (
  createOppSchema: Record<string, string>,
): Promise<CreateAnnouncementRecord> => {
  const response = await fetchAnnouncementWithMethod("POST")({
    body: createOppSchema,
  });
  const json = (await response.json()) as { data: CreateAnnouncementRecord };
  return json.data;
};

export async function createAnnouncementSummary({
  announcementId,
  body,
}: CreateAnnouncementSummaryParams): Promise<AnnouncementSummaryDetailApiResponse> {
  const response = await fetchAnnouncementWithMethod("POST")({
    subPath: `${announcementId}/summaries`,
    body,
    // want to allow responses with failed validations through so we can properly handle displaying validation errors
    allowedErrorStatuses: [422],
  });

  return (await response.json()) as AnnouncementSummaryDetailApiResponse;
}

export async function updateAnnouncementSummary({
  announcementId,
  announcementSummaryId,
  body,
}: UpdateAnnouncementSummaryParams): Promise<AnnouncementSummaryDetailApiResponse> {
  const response = await fetchAnnouncementWithMethod("PUT")({
    subPath: `${announcementId}/summaries/${announcementSummaryId}`,
    body,
    // want to allow responses with failed validations through so we can properly handle displaying validation errors
    allowedErrorStatuses: [422],
  });

  return (await response.json()) as AnnouncementSummaryDetailApiResponse;
}

export async function publishOpportunityForGrantor(
  opportunityId: string,
): Promise<GrantorAnnouncementApiResponse> {
  const response = await fetchAnnouncementWithMethod("POST")({
    subPath: `${opportunityId}/publish`,
  });

  return (await response.json()) as GrantorAnnouncementApiResponse;
}

export async function createApplicationPackage(
  announcementId: string,
  data: ApplicationPackageSaveRequest,
): Promise<ApplicationPackageSaveApiResponse> {
  const response = await fetchAnnouncementWithMethod("POST")({
    subPath: `${announcementId}/application-packages`,
    body: data,
  });
  return (await response.json()) as ApplicationPackageSaveApiResponse;
}

export async function updateApplicationPackage(
  announcementId: string,
  applicationPackageId: string,
  data: ApplicationPackageSaveRequest,
): Promise<ApplicationPackageSaveApiResponse> {
  const response = await fetchAnnouncementWithMethod("PUT")({
    subPath: `${announcementId}/application-packages/${applicationPackageId}`,
    body: data,
  });
  return (await response.json()) as ApplicationPackageSaveApiResponse;
}

export async function updateApplicationPackageForms({
  announcementId,
  applicationPackageId,
  body,
}: UpdateApplicationPackageFormsParams): Promise<ApplicationPackageFormsApiResponse> {
  const response = await fetchAnnouncementWithMethod("PUT")({
    subPath: `${announcementId}/application-packages/${applicationPackageId}/forms`,
    body,
  });
  return (await response.json()) as ApplicationPackageFormsApiResponse;
}

export async function saveCompetitionInstructions(
  opportunityId: string,
  competitionId: string,
  pendingFileId: string,
): Promise<ApplicationPackageInstructionsApiResponse> {
  const response = await fetchAnnouncementWithMethod("POST")({
    subPath: `${opportunityId}/application-packages/${competitionId}/instructions`,
    body: { pending_file_id: pendingFileId },
  });
  return (await response.json()) as ApplicationPackageInstructionsApiResponse;
}

export async function deleteCompetitionInstructions(
  opportunityId: string,
  competitionId: string,
  competitionInstructionId: string,
): Promise<APIResponse> {
  const response = await fetchAnnouncementWithMethod("DELETE")({
    subPath: `${opportunityId}/application-packages/${competitionId}/instructions/${competitionInstructionId}`,
  });
  return (await response.json()) as APIResponse;
}

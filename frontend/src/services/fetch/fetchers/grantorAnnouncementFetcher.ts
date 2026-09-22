"server-only";

import {
  fetchGrantorAgenciesWithMethod,
  fetchGrantorOpportunityWithMethod,
} from "src/services/fetch/fetchers/fetchers";
import {
  AnnouncementSummaryCreateRequest,
  AnnouncementSummaryDetailApiResponse,
  AnnouncementSummaryUpdateRequest,
  GrantorAnnouncementApiResponse,
} from "src/types/announcement/announcementResponseTypes";
import { APIResponse, PaginationInfo } from "src/types/apiResponseTypes";
import {
  ApplicationPackageInstructionsApiResponse,
  ApplicationPackageSaveApiResponse,
  ApplicationPackageSaveRequest,
} from "src/types/applicationPackageResponseTypes";
import { CreateAnnouncementRecord } from "src/types/createAnnouncementTypes";
import {
  PaginationRequestBody,
  SearchAPIResponse,
  SearchResponseData,
} from "src/types/search/searchRequestTypes";

type PaginationBody = {
  pagination: PaginationRequestBody;
};

type UpdateAnnoucementSummaryParams = {
  announcementId: string;
  announcementSummaryId: string;
  body: AnnouncementSummaryUpdateRequest;
};

type CreateAnnoucementSummaryParams = {
  announcementId: string;
  body: AnnouncementSummaryCreateRequest;
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

export const searchAccessibleOpportunities = async (
  pageInputs: PaginationRequestBody,
): Promise<{ data: SearchResponseData; pagination_info: PaginationInfo }> => {
  const response = await fetchGrantorOpportunityWithMethod("POST")({
    subPath: "list",
    body: { pagination: pageInputs },
  });

  return (await response.json()) as SearchAPIResponse;
};

export async function getAnnouncement(
  opportunityId: string,
): Promise<GrantorAnnouncementApiResponse> {
  const response = await fetchGrantorOpportunityWithMethod("GET")({
    subPath: opportunityId,
  });
  return (await response.json()) as GrantorAnnouncementApiResponse;
}

export const createOpportunity = async (
  createOppSchema: Record<string, string>,
): Promise<CreateAnnouncementRecord> => {
  const response = await fetchGrantorOpportunityWithMethod("POST")({
    body: createOppSchema,
  });
  const json = (await response.json()) as { data: CreateAnnouncementRecord };
  return json.data;
};

export async function createAnnoucementSummary({
  announcementId,
  body,
}: CreateAnnoucementSummaryParams): Promise<AnnouncementSummaryDetailApiResponse> {
  const response = await fetchGrantorOpportunityWithMethod("POST")({
    subPath: `${announcementId}/summaries`,
    body,
    // want to allow responses with failed validations through so we can properly handle displaying validation errors
    allowedErrorStatuses: [422],
  });

  return (await response.json()) as AnnouncementSummaryDetailApiResponse;
}

export async function updateAnnoucementSummary({
  announcementId,
  announcementSummaryId,
  body,
}: UpdateAnnoucementSummaryParams): Promise<AnnouncementSummaryDetailApiResponse> {
  const response = await fetchGrantorOpportunityWithMethod("PUT")({
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
  const response = await fetchGrantorOpportunityWithMethod("POST")({
    subPath: `${opportunityId}/publish`,
  });

  return (await response.json()) as GrantorAnnouncementApiResponse;
}

export async function createCompetitionForGrantor(
  opportunityId: string,
  data: ApplicationPackageSaveRequest,
): Promise<ApplicationPackageSaveApiResponse> {
  const response = await fetchGrantorOpportunityWithMethod("POST")({
    subPath: `${opportunityId}/application-packages`,
    body: data,
  });
  return (await response.json()) as ApplicationPackageSaveApiResponse;
}

export async function updateCompetitionForGrantor(
  opportunityId: string,
  competitionId: string,
  data: ApplicationPackageSaveRequest,
): Promise<ApplicationPackageSaveApiResponse> {
  const response = await fetchGrantorOpportunityWithMethod("PUT")({
    subPath: `${opportunityId}/application-packages/${competitionId}`,
    body: data,
  });
  return (await response.json()) as ApplicationPackageSaveApiResponse;
}

export async function saveCompetitionInstructions(
  opportunityId: string,
  competitionId: string,
  pendingFileId: string,
): Promise<ApplicationPackageInstructionsApiResponse> {
  const response = await fetchGrantorOpportunityWithMethod("POST")({
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
  const response = await fetchGrantorOpportunityWithMethod("DELETE")({
    subPath: `${opportunityId}/application-packages/${competitionId}/instructions/${competitionInstructionId}`,
  });
  return (await response.json()) as APIResponse;
}

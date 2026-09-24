import "server-only";

import {
  AnnouncementAttachmentCreateResponse,
  AnnouncementAttachmentListResponse,
} from "src/types/announcement/announcementAttachmentTypes";

import { fetchAnnouncementWithMethod } from "./fetchers";

export const listAnnouncementAttachments = async (
  opportunityId: string,
): Promise<AnnouncementAttachmentListResponse> => {
  const response = await fetchAnnouncementWithMethod("GET")({
    subPath: `${opportunityId}/attachments`,
  });
  return (await response.json()) as AnnouncementAttachmentListResponse;
};

export const createAnnouncementAttachment = async (
  opportunityId: string,
  pendingFileId: string,
): Promise<AnnouncementAttachmentCreateResponse> => {
  const response = await fetchAnnouncementWithMethod("POST")({
    subPath: `${opportunityId}/attachments`,
    body: { pending_file_id: pendingFileId },
    // want to allow responses with failed validations through so we can properly handle displaying validation errors
    allowedErrorStatuses: [422],
  });
  return (await response.json()) as AnnouncementAttachmentCreateResponse;
};

export const deleteOpportunityAttachment = async (
  opportunityId: string,
  attachmentId: string,
): Promise<{
  status_code: number;
  message: string;
  errors?: unknown[] | null;
}> => {
  const response = await fetchAnnouncementWithMethod("DELETE")({
    subPath: `${opportunityId}/attachments/${attachmentId}`,
    // want to allow responses with failed validations through so we can properly handle displaying validation errors
    allowedErrorStatuses: [422],
  });
  return (await response.json()) as {
    status_code: number;
    message: string;
    errors?: unknown[] | null;
  };
};

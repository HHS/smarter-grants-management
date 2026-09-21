import { APIResponse } from "src/types/apiResponseTypes";

export type AnnouncementAttachment = {
  opportunity_attachment_id: string;
  file_name: string;
  mime_type: string;
  file_size: number;
  created_at: string;
};

export interface AnnouncementAttachmentListResponse extends APIResponse {
  data: AnnouncementAttachment[];
}

export interface AnnouncementAttachmentCreateResponse extends APIResponse {
  data: AnnouncementAttachment;
}

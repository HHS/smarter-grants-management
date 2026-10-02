import { APIResponse } from "src/types/apiResponseTypes";

export type AnnouncementAttachment = {
  announcement_attachment_id: string;
  file_name: string;
  mime_type: string;
  file_size_bytes: number;
  file_description?: string | null;
  created_at: string;
  updated_at: string;
};

export interface AnnouncementAttachmentListResponse extends APIResponse {
  data: AnnouncementAttachment[];
}

export interface AnnouncementAttachmentCreateResponse extends APIResponse {
  data: AnnouncementAttachment;
}

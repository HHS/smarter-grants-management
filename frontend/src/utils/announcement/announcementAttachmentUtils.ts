import { UploadFileMetadata } from "src/types/fileUploadTypes";
import { AnnouncementAttachment } from "src/types/announcement/announcementAttachmentTypes";

// AnnouncementAttachment has no updated_at (only created_at) and no download_path
// (deferred to V2), unlike the apply-form Attachment type this mirrors.
const toFileMetadata = (
  attachment: AnnouncementAttachment,
): UploadFileMetadata => ({
  id: attachment.opportunity_attachment_id,
  fileName: attachment.file_name,
  fileSize: attachment.file_size,
  mimeType: attachment.mime_type,
  updatedAt: attachment.created_at,
});

export const mapAnnouncementAttachmentsToFileMetadata = (
  attachments: AnnouncementAttachment[],
): UploadFileMetadata[] =>
  attachments.map((attachment) => toFileMetadata(attachment));

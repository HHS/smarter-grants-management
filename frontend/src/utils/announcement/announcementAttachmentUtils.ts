import { AnnouncementAttachment } from "src/types/announcement/announcementAttachmentTypes";
import { UploadFileMetadata } from "src/types/fileUploadTypes";

// AnnouncementAttachment has no download_path (deferred to V2),
// unlike the apply-form Attachment type this mirrors.
const toFileMetadata = (
  attachment: AnnouncementAttachment,
): UploadFileMetadata => ({
  id: attachment.announcement_attachment_id,
  fileName: attachment.file_name,
  fileSize: attachment.file_size_bytes,
  mimeType: attachment.mime_type,
  updatedAt: attachment.updated_at,
});

export const mapAnnouncementAttachmentsToFileMetadata = (
  attachments: AnnouncementAttachment[],
): UploadFileMetadata[] =>
  attachments.map((attachment) => toFileMetadata(attachment));

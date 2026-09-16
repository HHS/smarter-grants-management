from typing import Any

from marshmallow import pre_dump

from src.api.schemas.extension import Schema, fields
from src.db.models.file_upload_models import FileAttachment


class FileAttachmentSchema(Schema):
    """Schema for our file attachment table - DOES NOT INCLUDE A DOWNLOAD PATH - see FileAttachmentDownloadSchema for that"""

    file_name = fields.String(
        metadata={"description": "The name of the attachment file", "example": "my_NOFO.pdf"}
    )
    file_size_bytes = fields.Integer(
        metadata={"description": "The size of the file in bytes", "example": 1024}
    )
    mime_type = fields.String(
        metadata={"description": "The MIME type of the attachment", "example": "application/pdf"}
    )

    file_description = fields.String(
        metadata={
            "description": "A description of the attachment",
            "example": "The full announcement NOFO",
        }
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @pre_dump
    def grab_file_attachment(self, record: Any, **kwargs: Any) -> Any:
        """
        Handle turning a many-to-many table that connects to the file_attachment table into just the file attachment

        For example, if we have a many-to-many table between announcement and file attachment, this
        can take in that many-to-many table and instead uses the file_attachment record on it instead
        of the many-to-many table in the response.
        """

        # Only return the file_attachment if its set + actually a file attachment,
        # otherwise just return the record as-is.
        file_attachment = getattr(record, "file_attachment", None)
        if file_attachment is not None and isinstance(file_attachment, FileAttachment):
            return file_attachment

        return record


class FileAttachmentDownloadSchema(FileAttachmentSchema):
    download_path = fields.String(
        metadata={
            "description": "The file's download path",
        },
    )

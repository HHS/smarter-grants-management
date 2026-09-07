from src.api.schemas.extension import Schema, fields, validators
from src.api.schemas.response_schema import AbstractResponseSchema
from src.constants.lookup_constants import FileScanStatus


class FileScanStatusUpdateRequestSchema(Schema):
    file_scan_status = fields.Enum(FileScanStatus, required=True)
    file_location = fields.String(
        required=True,
        validate=validators.Regexp(
            r"^s3://[^/]+/.+",
            error_message="file_location must be an s3:// path",
        ),
    )


class FileScanStatusUpdateResponseSchema(AbstractResponseSchema):
    pass


class CreatePresignedUploadRequestSchema(Schema):
    file_name = fields.String(
        required=True,
        validate=validators.Length(min=1, max=100),
    )
    mime_type = fields.String(required=True)


class PresignedUploadDataSchema(Schema):
    url = fields.String()
    body = fields.Dict()
    pending_file_id = fields.UUID()


class CreatePresignedUploadResponseSchema(AbstractResponseSchema):
    data = fields.Nested(PresignedUploadDataSchema)

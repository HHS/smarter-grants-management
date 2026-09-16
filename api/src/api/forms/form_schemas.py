from src.api.schemas.extension import Schema, fields
from src.api.schemas.response_schema import AbstractResponseSchema
from src.constants.lookup_constants import FormFamily


class FormSchema(Schema):

    form_id = fields.Integer(metadata={"description": "Unique identifier of the form"})

    agency_code = fields.String(
        metadata={"description": "The agency that owns the form", "example": "Grants.gov"}
    )

    name = fields.String(
        metadata={
            "description": "The full name of the form",
            "example": "Application for Federal Assistance (SF-424)",
        }
    )
    short_name = fields.String(
        metadata={"description": "The short name of the form", "example": "SF424"}
    )

    version = fields.String(metadata={"description": "The version of the form", "example": "4.0"})

    form_family = fields.List(
        fields.Enum(FormFamily),
        metadata={
            "description": "The form families that the form belongs to",
            "example": [FormFamily.SF_424],
        },
    )


class FormListResponseSchema(AbstractResponseSchema):
    data = fields.List(fields.Nested(FormSchema))

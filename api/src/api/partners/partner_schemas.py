from src.api.schemas.extension import Schema, fields
from src.api.schemas.response_schema import AbstractResponseSchema


class PartnerSchema(Schema):

    partner_id = fields.UUID(metadata={"description": "Unique ID of a partner"})

    partner_name = fields.String(
        metadata={"description": "Name of the partner", "example": "Department of Examples"}
    )


class GetPartnerResponseSchema(AbstractResponseSchema):
    data = fields.Nested(PartnerSchema)

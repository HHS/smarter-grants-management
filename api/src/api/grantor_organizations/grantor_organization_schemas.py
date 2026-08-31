from src.api.schemas.extension import Schema, fields
from src.api.schemas.response_schema import AbstractResponseSchema


class PartnerSchema(Schema):
    partner_id = fields.UUID(metadata={"description": "Unique ID of a partner"})
    partner_name = fields.String(metadata={"description": "Name of the partner"})


class GrantorOrganizationSchema(Schema):

    grantor_organization_id = fields.UUID(
        metadata={"description": "Unique ID of a grantor organization"}
    )

    organization_name = fields.String(
        metadata={
            "description": "Name of the grantor organization",
            "example": "My example organization",
        }
    )

    grantor_organization_type = fields.String(
        metadata={"description": "Type of grantor organization", "example": "grant_office"}
    )

    partner = fields.Nested(PartnerSchema)
    # Parent Organization provides one level up hierarchy
    parent_organization = fields.Nested(
        lambda: GrantorOrganizationSchema(exclude=("partner", "parent_organization")),
        allow_none=True,
    )


class GetGrantorOrganizationResponseSchema(AbstractResponseSchema):
    data = fields.Nested(GrantorOrganizationSchema)

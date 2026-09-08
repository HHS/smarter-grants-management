from src.api.grantor_organizations.grantor_organization_schemas import GrantorOrganizationSchema
from src.api.partners.partner_schemas import PartnerSchema
from src.api.schemas.extension import Schema, fields
from src.api.schemas.response_schema import AbstractResponseSchema


class ProgramSchema(Schema):

    program_id = fields.UUID(metadata={"description": "Unique ID of a program"})

    program_name = fields.String(
        metadata={"description": "Name of the program", "example": "My example program"}
    )

    partner = fields.Nested(PartnerSchema)

    program_office = fields.Nested(
        GrantorOrganizationSchema(exclude=("partner", "parent_organization"))
    )

    grant_office = fields.Nested(
        GrantorOrganizationSchema(exclude=("partner", "parent_organization"))
    )


class GetProgramResponseSchema(AbstractResponseSchema):
    data = fields.Nested(ProgramSchema)

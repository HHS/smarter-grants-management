from grants_shared.api.schemas.response_schema import AbstractResponseSchema
from grants_shared.api.schemas.extension import Schema, fields, validators
from grants_shared.api.schemas.search_schema import StrSearchSchemaBuilder
from grants_shared.pagination.pagination_schema import generate_pagination_schema

from src.constants.lookup_constants import MgmtPrivilege, ResourceInheritance


class ListUserForResourceFilterSchema(Schema):
    privilege = fields.Nested(
        StrSearchSchemaBuilder("PrivilegeFilterSchema")
        # TODO - we don't support a max length - need to fix in grants-shared
        .with_one_of(allowed_values=MgmtPrivilege)
        .build()
    )

    inheritance = fields.Nested(
        StrSearchSchemaBuilder("InheritanceFilterSchema")
        .with_one_of(allowed_values=ResourceInheritance)
        .build()
    )

class ListUserForResourceRequestSchema(Schema):
    filters = fields.Nested(ListUserForResourceFilterSchema())

    pagination = fields.Nested(
        generate_pagination_schema(
            "ListUserForResourcePaginationSchema",
            [
                "user_id", "email"
            ],
            default_sort_order=[{"order_by": "user_id", "sort_direction": "descending"}],
        ),
        required=True,
    )

class ListUserForResourceResponseSchema(AbstractResponseSchema):

    data = fields.MixinField(metadata={"example": None})
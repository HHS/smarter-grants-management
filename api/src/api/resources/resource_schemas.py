from grants_shared.api.schemas.extension import Schema, fields
from grants_shared.api.schemas.response_schema import AbstractResponseSchema, PaginationMixinSchema
from grants_shared.api.schemas.search_schema import StrSearchSchemaBuilder
from grants_shared.pagination.pagination_schema import generate_pagination_schema

from src.constants.lookup_constants import Privilege, ResourceInheritance, ResourceType


class ListUserForResourceFilterSchema(Schema):
    privilege = fields.Nested(
        StrSearchSchemaBuilder("PrivilegeFilterSchema")
        .with_one_of(allowed_values=Privilege)
        .build(),
        metadata={
            "description": "Only return users holding these privileges on the resource. A user must hold every privilege given, though not necessarily all from the same role."
        },
    )

    # A scalar rather than a one_of filter: asking for both full and direct at once has
    # no meaning, so there is nothing for a list to express.
    inheritance = fields.Enum(
        ResourceInheritance,
        load_default=ResourceInheritance.DIRECT,
        metadata={
            "description": "Whether to consider roles granted anywhere up the resource hierarchy ('full') or only on the resource itself ('direct')."
        },
    )


class ListUserForResourceRequestSchema(Schema):
    filters = fields.Nested(ListUserForResourceFilterSchema())

    pagination = fields.Nested(
        generate_pagination_schema(
            "ListUserForResourcePaginationSchema",
            ["user_id", "email"],
            default_sort_order=[{"order_by": "user_id", "sort_direction": "ascending"}],
        ),
        required=True,
    )


class ResourceForRoleSchema(Schema):
    """The resource a role was granted on."""

    resource_id = fields.UUID(metadata={"description": "The resource's unique identifier"})
    resource_name = fields.String(
        allow_none=True,
        metadata={
            "description": "The resource's name, if its type has one",
            "example": "Office of Grants",
        },
    )


class RoleForUserSchema(Schema):
    """A role a user holds, and the resource that granted it."""

    role_id = fields.UUID(metadata={"description": "The role's unique identifier"})
    role_name = fields.String(
        metadata={"description": "The role's name", "example": "Program Officer"}
    )
    privileges = fields.List(
        fields.Enum(Privilege),
        metadata={"description": "The privileges the role carries"},
    )
    resource_type = fields.Enum(
        ResourceType,
        metadata={"description": "The type of resource the role was granted on"},
    )
    resource = fields.Nested(
        ResourceForRoleSchema,
        metadata={"description": "The resource the role was granted on"},
    )


class UserForResourceSchema(Schema):
    user_id = fields.UUID(metadata={"description": "The user's unique identifier"})
    email = fields.String(
        allow_none=True,
        metadata={
            "description": "The user's email address, null if they have no login",
            "example": "user@example.com",
        },
    )
    roles = fields.List(
        fields.Nested(RoleForUserSchema),
        metadata={"description": "The roles granting this user access to the resource"},
    )


class ListUserForResourceResponseSchema(AbstractResponseSchema, PaginationMixinSchema):
    data = fields.List(
        fields.Nested(UserForResourceSchema),
        metadata={"description": "The users with access to the resource"},
    )

from typing import Any

from grants_shared.api.schemas.extension import (
    MarshmallowErrorContainer,
    Schema,
    SchemaValidationError,
    fields,
)
from grants_shared.api.schemas.response_schema import AbstractResponseSchema, PaginationMixinSchema
from grants_shared.api.schemas.search_schema import StrSearchSchemaBuilder
from grants_shared.pagination.pagination_schema import generate_pagination_schema
from marshmallow import ValidationError, validates_schema

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

    # Shaped as a one_of like every other filter, so the nesting sits at the same layer
    # throughout - even though only one value is meaningful. Asking for both full and
    # direct at once has no meaning, so more than one value is rejected below rather than
    # silently ignored.
    inheritance = fields.Nested(
        StrSearchSchemaBuilder("InheritanceFilterSchema")
        .with_one_of(allowed_values=ResourceInheritance)
        .build(),
        metadata={
            "description": "Whether to consider roles granted anywhere up the resource hierarchy ('full') or only on the resource itself ('direct'). Accepts a single value, and defaults to 'direct'."
        },
    )

    @validates_schema
    def validate_single_inheritance(self, data: dict[str, Any], **kwargs: Any) -> None:
        """Reject more than one inheritance value.

        Belongs on the builder as a maximum length rather than here - that needs a
        grants-shared change, which is tracked separately.
        """
        one_of = (data.get("inheritance") or {}).get("one_of") or []
        if len(one_of) > 1:
            raise ValidationError(
                [
                    MarshmallowErrorContainer(
                        SchemaValidationError.MAX_LENGTH,
                        "inheritance supports at most 1 value",
                    )
                ],
                "inheritance",
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

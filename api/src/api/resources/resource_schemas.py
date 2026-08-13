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

from src.constants.lookup_constants import MgmtPrivilege, MgmtResourceType, ResourceInheritance


class ListUserForResourceFilterSchema(Schema):
    privilege = fields.Nested(
        StrSearchSchemaBuilder("PrivilegeFilterSchema")
        .with_one_of(allowed_values=MgmtPrivilege)
        .build(),
        metadata={
            "description": "Only return users holding this privilege on the resource. A user must hold every privilege given."
        },
    )

    inheritance = fields.Nested(
        StrSearchSchemaBuilder("InheritanceFilterSchema")
        .with_one_of(allowed_values=ResourceInheritance)
        .build(),
        metadata={
            "description": "Whether to consider roles granted anywhere up the resource hierarchy ('full') or only on the resource itself ('direct'). Defaults to 'direct'."
        },
    )

    # StrSearchSchemaBuilder can't express a maximum length on a one_of, so the caps the
    # API contract promises are enforced here. Note the underlying query handles any
    # number of privileges (a user must hold all of them) - the cap is an API-surface
    # decision we can widen later, not a limitation of the lookup.
    _MAX_VALUES_PER_FILTER = 1

    @validates_schema
    def validate_filter_lengths(self, data: dict[str, Any], **kwargs: Any) -> None:
        for field_name in ("privilege", "inheritance"):
            one_of = (data.get(field_name) or {}).get("one_of") or []
            if len(one_of) > self._MAX_VALUES_PER_FILTER:
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.MAX_LENGTH,
                            f"{field_name} supports at most {self._MAX_VALUES_PER_FILTER} value",
                        )
                    ],
                    field_name,
                )


class ListUserForResourceRequestSchema(Schema):
    filters = fields.Nested(ListUserForResourceFilterSchema())

    pagination = fields.Nested(
        generate_pagination_schema(
            "ListUserForResourcePaginationSchema",
            ["mgmt_user_id", "email"],
            default_sort_order=[{"order_by": "mgmt_user_id", "sort_direction": "ascending"}],
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

    mgmt_role_id = fields.UUID(metadata={"description": "The role's unique identifier"})
    role_name = fields.String(
        metadata={"description": "The role's name", "example": "Program Officer"}
    )
    privileges = fields.List(
        fields.Enum(MgmtPrivilege),
        metadata={"description": "The privileges the role carries"},
    )
    resource_type = fields.Enum(
        MgmtResourceType,
        metadata={"description": "The type of resource the role was granted on"},
    )
    resource = fields.Nested(
        ResourceForRoleSchema,
        metadata={"description": "The resource the role was granted on"},
    )


class UserForResourceSchema(Schema):
    mgmt_user_id = fields.UUID(metadata={"description": "The user's unique identifier"})
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

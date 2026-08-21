from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.db.lookup import Lookup, LookupConfig, LookupRegistry, LookupStr, LookupTable
from src.constants.lookup_constants import (
    ApprovalResponseType,
    ApprovalType,
    ExternalUserType,
    GrantorOrganizationType,
    Privilege,
    ResourceType,
    UserType,
    WorkflowType,
)
from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable

#######################################################
# LookupConfig mappings
#
# Put all mappings of lookup values to their DB integer
# representations in this section
#######################################################

USER_TYPE_CONFIG: LookupConfig[UserType] = LookupConfig(
    [
        LookupStr(UserType.STANDARD, 1),
        LookupStr(UserType.INTERNAL_FRONTEND, 2),
    ]
)

EXTERNAL_USER_TYPE_CONFIG: LookupConfig[ExternalUserType] = LookupConfig(
    [LookupStr(ExternalUserType.LOGIN_GOV, 1)]
)

PRIVILEGE_CONFIG: LookupConfig[Privilege] = LookupConfig(
    [
        LookupStr(Privilege.VIEW_PARTNER, 1),
        LookupStr(Privilege.UPDATE_PARTNER, 2),
        LookupStr(Privilege.MANAGE_PARTNER_MEMBERS, 3),
        LookupStr(Privilege.VIEW_PROGRAM, 4),
        LookupStr(Privilege.UPDATE_PROGRAM, 5),
        LookupStr(Privilege.INTERNAL_WORKFLOW_EVENT_SEND, 6),
        LookupStr(Privilege.VIEW_GRANTOR_ORGANIZATION, 7),
        LookupStr(Privilege.UPDATE_GRANTOR_ORGANIZATION, 8),
        LookupStr(Privilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS, 9),
        LookupStr(Privilege.UNUSED_PRIVILEGE_102, 10),
        LookupStr(Privilege.UNUSED_PRIVILEGE_103, 11),
    ]
)

RESOURCE_TYPE_CONFIG: LookupConfig[ResourceType] = LookupConfig(
    [
        LookupStr(ResourceType.INTERNAL, 1),
        LookupStr(ResourceType.PARTNER, 2),
        LookupStr(ResourceType.PROGRAM, 3),
        LookupStr(ResourceType.GRANTOR_ORGANIZATION, 4),
        LookupStr(ResourceType.OPPORTUNITY, 5),
    ]
)

GRANTOR_ORGANIZATION_TYPE_CONFIG: LookupConfig[GrantorOrganizationType] = LookupConfig(
    [
        LookupStr(GrantorOrganizationType.PROGRAM_OFFICE, 1),
        LookupStr(GrantorOrganizationType.GRANT_OFFICE, 2),
    ]
)

# Only the values the engine itself needs are seeded here. The find/apply workflow
# and approval types (opportunity_publish, award recommendation review, and so on)
# are deliberately not ported - teams add values as they build real  workflows.
WORKFLOW_TYPE_CONFIG: LookupConfig[WorkflowType] = LookupConfig(
    [
        LookupStr(WorkflowType.BASIC_TEST_WORKFLOW, 1),
        LookupStr(WorkflowType.PROTOTYPE_WORKFLOW, 2),
        LookupStr(WorkflowType.APPROVAL_TEST_WORKFLOW, 3),
        LookupStr(WorkflowType.LIMITED_APPROVAL_TEST_WORKFLOW, 4),
    ]
)

APPROVAL_TYPE_CONFIG: LookupConfig[ApprovalType] = LookupConfig(
    [
        LookupStr(ApprovalType.BASIC_TEST_APPROVAL, 1),
        LookupStr(ApprovalType.SECONDARY_TEST_APPROVAL, 2),
    ]
)

APPROVAL_RESPONSE_TYPE_CONFIG: LookupConfig[ApprovalResponseType] = LookupConfig(
    [
        LookupStr(ApprovalResponseType.APPROVED, 1),
        LookupStr(ApprovalResponseType.DECLINED, 2),
        LookupStr(ApprovalResponseType.REQUIRES_MODIFICATION, 3),
    ]
)

#######################################################
# GrantorLookupTable
#
# Base table that all lookup tables are derived from
#######################################################


class GrantorLookupTable(LookupTable, GrantorSchemaTable):
    """
    Base lookup table class that includes the GrantorSchemasTable as well
    so that the tables end up in the grantor schema.
    """

    __abstract__ = True


#######################################################
# Lookup Tables
#
# Put all lookup table definitions in this section and
# connect them to the lookup configurations defined above
#######################################################


@LookupRegistry.register_lookup(USER_TYPE_CONFIG)
class LkUserType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_user_type"

    user_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkUserType:
        return LkUserType(user_type_id=lookup.lookup_val, description=lookup.get_description())


@LookupRegistry.register_lookup(EXTERNAL_USER_TYPE_CONFIG)
class LkExternalUserType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_external_user_type"

    external_user_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkExternalUserType:
        return LkExternalUserType(
            external_user_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(PRIVILEGE_CONFIG)
class LkPrivilege(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_privilege"

    privilege_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkPrivilege:
        return LkPrivilege(privilege_id=lookup.lookup_val, description=lookup.get_description())


@LookupRegistry.register_lookup(RESOURCE_TYPE_CONFIG)
class LkResourceType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_resource_type"

    resource_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkResourceType:
        return LkResourceType(
            resource_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(GRANTOR_ORGANIZATION_TYPE_CONFIG)
class LkGrantorOrganizationType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_grantor_organization_type"

    grantor_organization_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkGrantorOrganizationType:
        return LkGrantorOrganizationType(
            grantor_organization_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(WORKFLOW_TYPE_CONFIG)
class LkWorkflowType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_workflow_type"

    workflow_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkWorkflowType:
        return LkWorkflowType(
            workflow_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(APPROVAL_TYPE_CONFIG)
class LkApprovalType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_approval_type"

    approval_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkApprovalType:
        return LkApprovalType(
            approval_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(APPROVAL_RESPONSE_TYPE_CONFIG)
class LkApprovalResponseType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_approval_response_type"

    approval_response_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkApprovalResponseType:
        return LkApprovalResponseType(
            approval_response_type_id=lookup.lookup_val, description=lookup.get_description()
        )

from grants_shared.db.models.base import TimestampMixin
from grants_shared.db.models.lookup import (
    Lookup,
    LookupConfig,
    LookupRegistry,
    LookupStr,
    LookupTable,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.constants.lookup_constants import (
    ExternalUserType,
    GrantorOrganizationType,
    MgmtApprovalResponseType,
    MgmtApprovalType,
    MgmtPrivilege,
    MgmtResourceType,
    MgmtUserType,
    MgmtWorkflowType,
)
from src.db.models.grantor_schema_table import GrantorSchemaTable

#######################################################
# LookupConfig mappings
#
# Put all mappings of lookup values to their DB integer
# representations in this section
#######################################################

MGMT_USER_TYPE_CONFIG: LookupConfig[MgmtUserType] = LookupConfig(
    [
        LookupStr(MgmtUserType.STANDARD, 1),
        LookupStr(MgmtUserType.INTERNAL_FRONTEND, 2),
    ]
)

EXTERNAL_USER_TYPE_CONFIG: LookupConfig[ExternalUserType] = LookupConfig(
    [LookupStr(ExternalUserType.LOGIN_GOV, 1)]
)

MGMT_PRIVILEGE_CONFIG: LookupConfig[MgmtPrivilege] = LookupConfig(
    [
        LookupStr(MgmtPrivilege.VIEW_PARTNER, 1),
        LookupStr(MgmtPrivilege.UPDATE_PARTNER, 2),
        LookupStr(MgmtPrivilege.MANAGE_PARTNER_MEMBERS, 3),
        LookupStr(MgmtPrivilege.VIEW_PROGRAM, 4),
        LookupStr(MgmtPrivilege.UPDATE_PROGRAM, 5),
        LookupStr(MgmtPrivilege.UNUSED_PRIVILEGE_101, 6),
        LookupStr(MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION, 7),
        LookupStr(MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION, 8),
        LookupStr(MgmtPrivilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS, 9),
        LookupStr(MgmtPrivilege.UNUSED_PRIVILEGE_102, 10),
        LookupStr(MgmtPrivilege.UNUSED_PRIVILEGE_103, 11),
    ]
)

MGMT_RESOURCE_TYPE_CONFIG: LookupConfig[MgmtResourceType] = LookupConfig(
    [
        LookupStr(MgmtResourceType.INTERNAL, 1),
        LookupStr(MgmtResourceType.PARTNER, 2),
        LookupStr(MgmtResourceType.PROGRAM, 3),
        LookupStr(MgmtResourceType.GRANTOR_ORGANIZATION, 4),
        LookupStr(MgmtResourceType.OPPORTUNITY, 5),
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
# are deliberately not ported - teams add values as they build real mgmt workflows.
MGMT_WORKFLOW_TYPE_CONFIG: LookupConfig[MgmtWorkflowType] = LookupConfig(
    [
        LookupStr(MgmtWorkflowType.BASIC_TEST_WORKFLOW, 1),
    ]
)

MGMT_APPROVAL_TYPE_CONFIG: LookupConfig[MgmtApprovalType] = LookupConfig(
    [
        LookupStr(MgmtApprovalType.BASIC_TEST_APPROVAL, 1),
    ]
)

MGMT_APPROVAL_RESPONSE_TYPE_CONFIG: LookupConfig[MgmtApprovalResponseType] = LookupConfig(
    [
        LookupStr(MgmtApprovalResponseType.APPROVED, 1),
        LookupStr(MgmtApprovalResponseType.DECLINED, 2),
        LookupStr(MgmtApprovalResponseType.REQUIRES_MODIFICATION, 3),
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


@LookupRegistry.register_lookup(MGMT_USER_TYPE_CONFIG)
class LkMgmtUserType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_mgmt_user_type"

    mgmt_user_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkMgmtUserType:
        return LkMgmtUserType(
            mgmt_user_type_id=lookup.lookup_val, description=lookup.get_description()
        )


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


@LookupRegistry.register_lookup(MGMT_PRIVILEGE_CONFIG)
class LkMgmtPrivilege(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_mgmt_privilege"

    mgmt_privilege_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkMgmtPrivilege:
        return LkMgmtPrivilege(
            mgmt_privilege_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(MGMT_RESOURCE_TYPE_CONFIG)
class LkMgmtResourceType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_mgmt_resource_type"

    mgmt_resource_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkMgmtResourceType:
        return LkMgmtResourceType(
            mgmt_resource_type_id=lookup.lookup_val, description=lookup.get_description()
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


@LookupRegistry.register_lookup(MGMT_WORKFLOW_TYPE_CONFIG)
class LkMgmtWorkflowType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_mgmt_workflow_type"

    mgmt_workflow_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkMgmtWorkflowType:
        return LkMgmtWorkflowType(
            mgmt_workflow_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(MGMT_APPROVAL_TYPE_CONFIG)
class LkMgmtApprovalType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_mgmt_approval_type"

    mgmt_approval_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkMgmtApprovalType:
        return LkMgmtApprovalType(
            mgmt_approval_type_id=lookup.lookup_val, description=lookup.get_description()
        )


@LookupRegistry.register_lookup(MGMT_APPROVAL_RESPONSE_TYPE_CONFIG)
class LkMgmtApprovalResponseType(GrantorLookupTable, TimestampMixin):
    __tablename__ = "lk_mgmt_approval_response_type"

    mgmt_approval_response_type_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]

    @classmethod
    def from_lookup(cls, lookup: Lookup) -> LkMgmtApprovalResponseType:
        return LkMgmtApprovalResponseType(
            mgmt_approval_response_type_id=lookup.lookup_val, description=lookup.get_description()
        )

from enum import StrEnum


class JobType(StrEnum):
    MIGRATE_UP = "migrate-up"
    MIGRATE_DOWN = "migrate-down"
    MIGRATE_DOWNALL = "migrate-downall"


class MgmtUserType(StrEnum):
    STANDARD = "standard"
    INTERNAL_FRONTEND = "internal_frontend"


class ExternalUserType(StrEnum):
    LOGIN_GOV = "login_gov"


class MgmtPrivilege(StrEnum):
    VIEW_PARTNER = "view_partner"
    UPDATE_PARTNER = "update_partner"
    MANAGE_PARTNER_MEMBERS = "manage_partner_members"

    VIEW_PROGRAM = "view_program"
    UPDATE_PROGRAM = "update_program"

    VIEW_GRANTOR_ORGANIZATION = "view_grantor_organization"
    UPDATE_GRANTOR_ORGANIZATION = "update_grantor_organization"
    MANAGE_GRANTOR_ORGANIZATION_MEMBERS = "manage_grantor_organization_members"

    # NOTE - if you need to add any new privileges, you can
    # rename these ones first. Our lookup logic doesn't allow
    # for deleting lookup values, but does let you rename.
    # These haven't ever been used, so are safe to rename and reuse.
    UNUSED_PRIVILEGE_101 = "unused_privilege_101"
    UNUSED_PRIVILEGE_102 = "unused_privilege_102"
    UNUSED_PRIVILEGE_103 = "unused_privilege_103"


class MgmtResourceType(StrEnum):
    INTERNAL = "internal"
    PARTNER = "partner"
    PROGRAM = "program"
    GRANTOR_ORGANIZATION = "grantor_organization"
    OPPORTUNITY = "opportunity"


class GrantorOrganizationType(StrEnum):
    PROGRAM_OFFICE = "program_office"
    GRANT_OFFICE = "grant_office"


class MgmtWorkflowType(StrEnum):
    # Because of how we use the workflow type to find
    # the state machine and its configuration, we need
    # to define any workflows for tests here as well.
    # This workflow type isn't real, and is instead
    # reserved for the prototype state machine and tests.
    BASIC_TEST_WORKFLOW = "basic_test_workflow"

    # Also not real - backs a test-only state machine configured to disallow
    # concurrent workflows, since the prototype allows them.
    NO_CONCURRENT_TEST_WORKFLOW = "no_concurrent_test_workflow"

    def get_human_friendly_text(self) -> str:
        return self.value.replace("_", " ").title()


class MgmtApprovalType(StrEnum):
    BASIC_TEST_APPROVAL = "basic_test_approval"


class MgmtApprovalResponseType(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"
    REQUIRES_MODIFICATION = "requires_modification"


class MgmtWorkflowEventType(StrEnum):
    START_WORKFLOW = "start_workflow"
    PROCESS_WORKFLOW = "process_workflow"


class MgmtWorkflowEventProcessingResult(StrEnum):
    """Enum representing the result of processing an SQS event."""

    SUCCESS = "success"
    NON_RETRYABLE_ERROR = "non_retryable_error"
    RETRYABLE_ERROR = "retryable_error"
    GENERAL_ERROR = "general_error"


# The resource types each privilege is allowed to be assigned at. A privilege may only be
# included in a role when the role's resource types are a subset of the privilege's allowed
# resource types (validated in src/util/role_util.py::build_role). This prevents assigning,
# for example, a department-only privilege on a team-level role.
ALLOWED_RESOURCES_FOR_PRIVILEGE: dict[MgmtPrivilege, set[MgmtResourceType]] = {
    # Partner-level
    MgmtPrivilege.VIEW_PARTNER: {MgmtResourceType.PARTNER},
    MgmtPrivilege.UPDATE_PARTNER: {MgmtResourceType.PARTNER},
    MgmtPrivilege.MANAGE_PARTNER_MEMBERS: {MgmtResourceType.PARTNER},
    # Program-level
    MgmtPrivilege.VIEW_PROGRAM: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
        MgmtResourceType.PROGRAM,
    },
    MgmtPrivilege.UPDATE_PROGRAM: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
        MgmtResourceType.PROGRAM,
    },
    # Grantor organization level
    MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
    },
    MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
    },
    MgmtPrivilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS: {
        MgmtResourceType.PARTNER,
        MgmtResourceType.GRANTOR_ORGANIZATION,
    },
    MgmtPrivilege.UNUSED_PRIVILEGE_101: set(),
    MgmtPrivilege.UNUSED_PRIVILEGE_102: set(),
    MgmtPrivilege.UNUSED_PRIVILEGE_103: set(),
}

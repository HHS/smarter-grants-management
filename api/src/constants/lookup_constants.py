from enum import StrEnum


class JobType(StrEnum):
    MIGRATE_UP = "migrate-up"
    MIGRATE_DOWN = "migrate-down"
    MIGRATE_DOWNALL = "migrate-downall"
    FETCH_ASSISTANCE_LISTING = "fetch-assistance-listing"


class UserType(StrEnum):
    STANDARD = "standard"
    INTERNAL_FRONTEND = "internal_frontend"


class ExternalUserType(StrEnum):
    LOGIN_GOV = "login_gov"


class Privilege(StrEnum):
    VIEW_PARTNER = "view_partner"
    UPDATE_PARTNER = "update_partner"
    MANAGE_PARTNER_MEMBERS = "manage_partner_members"

    VIEW_PROGRAM = "view_program"
    UPDATE_PROGRAM = "update_program"

    VIEW_GRANTOR_ORGANIZATION = "view_grantor_organization"
    UPDATE_GRANTOR_ORGANIZATION = "update_grantor_organization"
    MANAGE_GRANTOR_ORGANIZATION_MEMBERS = "manage_grantor_organization_members"

    # Internal-only privilege for sending workflow events directly to the event API.
    # It exists so we can drive workflows ourselves for testing, not for real grantor users.
    INTERNAL_WORKFLOW_EVENT_SEND = "internal_workflow_event_send"

    # NOTE - if you need to add any new privileges, you can
    # rename these ones first. Our lookup logic doesn't allow
    # for deleting lookup values, but does let you rename.
    # These haven't ever been used, so are safe to rename and reuse.
    UNUSED_PRIVILEGE_102 = "unused_privilege_102"
    UNUSED_PRIVILEGE_103 = "unused_privilege_103"


class ResourceType(StrEnum):
    INTERNAL = "internal"
    PARTNER = "partner"
    PROGRAM = "program"
    GRANTOR_ORGANIZATION = "grantor_organization"
    OPPORTUNITY = "opportunity"


class GrantorOrganizationType(StrEnum):
    PROGRAM_OFFICE = "program_office"
    GRANT_OFFICE = "grant_office"


class PartnerAuditEvent(StrEnum):
    USER_ROLES_MODIFIED = "user_roles_modified"


class GrantorOrganizationAuditEvent(StrEnum):
    USER_ROLES_MODIFIED = "user_roles_modified"


class WorkflowType(StrEnum):
    # Because of how we use the workflow type to find
    # the state machine and its configuration, we need
    # to define any workflows for tests here as well.
    # This workflow type isn't real - it backs the state machine
    # our engine tests run against.
    BASIC_TEST_WORKFLOW = "basic_test_workflow"

    # Also not real - backs the prototype state machine, which exists to prove the
    # engine works end to end until the first real grantor workflow lands.
    PROTOTYPE_WORKFLOW = "prototype_workflow"

    # Also not real - back the test-only state machines that exercise approvals,
    # which neither the basic test machine nor the prototype configures.
    APPROVAL_TEST_WORKFLOW = "approval_test_workflow"
    LIMITED_APPROVAL_TEST_WORKFLOW = "limited_approval_test_workflow"

    def get_human_friendly_text(self) -> str:
        return self.value.replace("_", " ").title()


class ApprovalType(StrEnum):
    # As with the workflow types above, real approval types arrive with the real
    # workflows - these two exist so the approval machinery can be tested, and
    # having two of them is what lets us cover a user doing more than one kind of
    # approval on the same workflow.
    BASIC_TEST_APPROVAL = "basic_test_approval"
    SECONDARY_TEST_APPROVAL = "secondary_test_approval"


class ApprovalResponseType(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"
    REQUIRES_MODIFICATION = "requires_modification"


class WorkflowEventType(StrEnum):
    START_WORKFLOW = "start_workflow"
    PROCESS_WORKFLOW = "process_workflow"


class WorkflowEventProcessingResult(StrEnum):
    """Enum representing the result of processing an SQS event."""

    SUCCESS = "success"
    NON_RETRYABLE_ERROR = "non_retryable_error"
    RETRYABLE_ERROR = "retryable_error"
    GENERAL_ERROR = "general_error"


class FileScanStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    INFECTED = "infected"
    PROCESSED = "processed"


class ResourceInheritance(StrEnum):
    """How far up the resource hierarchy a user lookup should reach.

    Not a lookup table - this is an API filter value, so it has no DB representation.
    """

    # Every resource from the one asked about up through the hierarchy, matching what
    # AuthorizationEnforcer.can_access considers.
    FULL = "full"

    # Only roles granted on the resource itself. Note that a program is a special case
    # (users are never attached to programs).
    DIRECT = "direct"


# The resource types each privilege is allowed to be assigned at. A privilege may only be
# included in a role when the role's resource types are a subset of the privilege's allowed
# resource types (validated in src/util/role_util.py::build_role). This prevents assigning,
# for example, a department-only privilege on a team-level role.
ALLOWED_RESOURCES_FOR_PRIVILEGE: dict[Privilege, set[ResourceType]] = {
    # Partner-level
    Privilege.VIEW_PARTNER: {ResourceType.PARTNER},
    Privilege.UPDATE_PARTNER: {ResourceType.PARTNER},
    Privilege.MANAGE_PARTNER_MEMBERS: {ResourceType.PARTNER},
    # Program-level
    Privilege.VIEW_PROGRAM: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
        ResourceType.PROGRAM,
    },
    Privilege.UPDATE_PROGRAM: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
        ResourceType.PROGRAM,
    },
    # Grantor organization level
    Privilege.VIEW_GRANTOR_ORGANIZATION: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
    },
    Privilege.UPDATE_GRANTOR_ORGANIZATION: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
    },
    Privilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
    },
    # Internal-only
    Privilege.INTERNAL_WORKFLOW_EVENT_SEND: {ResourceType.INTERNAL},
    Privilege.UNUSED_PRIVILEGE_102: set(),
    Privilege.UNUSED_PRIVILEGE_103: set(),
}

# The privilege a caller needs to view a resource of a given type. Also defines which
# resource types read access can be resolved for at all - deliberately narrower than
# every ResourceType, with the others added as we need them. Shared by anything that
# authorizes off a resource's type rather than an explicit privilege sent by the
# caller (listing a resource's users, reading a workflow attached to a resource, ...).
VIEW_PRIVILEGE_FOR_RESOURCE_TYPE: dict[ResourceType, Privilege] = {
    ResourceType.PARTNER: Privilege.VIEW_PARTNER,
    ResourceType.GRANTOR_ORGANIZATION: Privilege.VIEW_GRANTOR_ORGANIZATION,
    ResourceType.PROGRAM: Privilege.VIEW_PROGRAM,
}

import pytest

from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import (
    ApprovalResponseType,
    ApprovalType,
    Privilege,
    WorkflowType,
)
from src.workflow.service.approval_service import (
    can_user_do_approval,
    get_approval_response_type_from_metadata,
    get_approvals_for_workflow,
    validate_approval_response_type,
)
from src.workflow.workflow_config import ApprovalConfig
from src.workflow.workflow_errors import (
    DisallowedApprovalResponseTypeError,
    InvalidWorkflowResponseTypeError,
)
from tests.db.models.factories import (
    ProgramFactory,
    ProgramWorkflowFactory,
    UserFactory,
    WorkflowApprovalFactory,
)
from tests.workflow.state_machine.test_state_machines import (
    ApprovalTestStateMachine,
    approval_test_workflow_config,
)
from tests.workflow.workflow_test_util import create_approver

PRIMARY_APPROVAL_EVENT = "receive_primary_approval"
SECONDARY_APPROVAL_EVENT = "receive_secondary_approval"


def verify_can_do_only(db_session, user, workflow, expected_allowed_events: set[str]):
    """Verify a user can do exactly the approval events we expect and no others."""
    for event in ApprovalTestStateMachine.get_valid_events():
        result = can_user_do_approval(
            db_session=db_session,
            user=user,
            workflow=workflow,
            config=approval_test_workflow_config,
            event_to_send=event,
        )

        if event in expected_allowed_events:
            assert result is True, f"Expected user to be able to do {event}"
        else:
            assert result is False, f"Expected user to NOT be able to do {event}"


def test_can_user_do_approval_with_qualifying_role(
    db_session, program, primary_approver, secondary_approver
):
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW, program=program
    )

    # Each approver can only do the approval their privilege is configured for
    verify_can_do_only(
        db_session, primary_approver, workflow, expected_allowed_events={PRIMARY_APPROVAL_EVENT}
    )
    verify_can_do_only(
        db_session, secondary_approver, workflow, expected_allowed_events={SECONDARY_APPROVAL_EVENT}
    )


def test_can_user_do_approval_with_multiple_privileges(db_session, program):
    user = create_approver(
        db_session,
        program.grant_office,
        privileges=[Privilege.UPDATE_PROGRAM, Privilege.VIEW_PROGRAM],
    )

    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW, program=program
    )

    verify_can_do_only(
        db_session,
        user,
        workflow,
        expected_allowed_events={PRIMARY_APPROVAL_EVENT, SECONDARY_APPROVAL_EVENT},
    )


def test_can_user_do_approval_user_with_no_roles(db_session, program, enable_factory_create):
    user = UserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW, program=program
    )

    verify_can_do_only(db_session, user, workflow, expected_allowed_events=set())


def test_can_user_do_approval_role_on_another_resource(db_session, program, enable_factory_create):
    """A role on some unrelated program's office grants nothing here."""
    other_program_user = create_approver(
        db_session, ProgramFactory.create().grant_office, privileges=[Privilege.UPDATE_PROGRAM]
    )

    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW, program=program
    )

    verify_can_do_only(db_session, other_program_user, workflow, expected_allowed_events=set())


def test_can_user_do_approval_inherited_privilege_is_not_enough(
    db_session, program, inherited_privilege_user
):
    """Pin the v1 limitation: privileges from a parent resource do not allow approving.

    The authorization layer itself says this user can act on the program - the approval
    check deliberately disagrees, because it looks the resource up with DIRECT
    inheritance. When the follow-up work widens that to FULL, this assertion flips.
    """
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW, program=program
    )

    # The hierarchy-aware authZ check does grant this user access to the program
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user=inherited_privilege_user,
            required_privileges={Privilege.UPDATE_PROGRAM},
            resource=program,
        )
        is True
    )

    # ...but the v1 approval check does not
    verify_can_do_only(
        db_session, inherited_privilege_user, workflow, expected_allowed_events=set()
    )


def test_can_user_do_approval_event_without_approval_config(db_session, program, primary_approver):
    """An event with no approval config is never an approval a user can do."""
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW, program=program
    )

    assert (
        can_user_do_approval(
            db_session=db_session,
            user=primary_approver,
            workflow=workflow,
            config=approval_test_workflow_config,
            event_to_send="middle_to_end",
        )
        is False
    )


####################
# get_approvals_for_workflow
####################


def test_get_approvals_for_workflow_filters(db_session, program, enable_factory_create):
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW, program=program
    )
    other_workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW, program=program
    )

    user = UserFactory.create()
    other_user = UserFactory.create()

    valid_approval = WorkflowApprovalFactory.create(
        workflow=workflow,
        approving_user=user,
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        is_still_valid=True,
    )
    other_user_approval = WorkflowApprovalFactory.create(
        workflow=workflow,
        approving_user=other_user,
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        is_still_valid=True,
    )
    # Filtered out - no longer valid
    WorkflowApprovalFactory.create(
        workflow=workflow,
        approving_user=user,
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        is_still_valid=False,
    )
    # Filtered out - different approval type
    WorkflowApprovalFactory.create(
        workflow=workflow,
        approving_user=user,
        approval_type=ApprovalType.SECONDARY_TEST_APPROVAL,
        is_still_valid=True,
    )
    # Filtered out - different workflow
    WorkflowApprovalFactory.create(
        workflow=other_workflow,
        approving_user=user,
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        is_still_valid=True,
    )

    approvals = get_approvals_for_workflow(
        db_session=db_session,
        workflow=workflow,
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
    )
    assert {approval.workflow_approval_id for approval in approvals} == {
        valid_approval.workflow_approval_id,
        other_user_approval.workflow_approval_id,
    }

    # Filtering to a user narrows it further
    user_approvals = get_approvals_for_workflow(
        db_session=db_session,
        workflow=workflow,
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        approving_user=user,
    )
    assert [approval.workflow_approval_id for approval in user_approvals] == [
        valid_approval.workflow_approval_id
    ]

    # And invalid approvals come back when we ask for them
    all_approvals = get_approvals_for_workflow(
        db_session=db_session,
        workflow=workflow,
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        approving_user=user,
        is_valid_events=False,
    )
    assert len(all_approvals) == 2


####################
# Approval response type handling
####################


@pytest.mark.parametrize(
    "response_type",
    [
        ApprovalResponseType.APPROVED,
        ApprovalResponseType.DECLINED,
        ApprovalResponseType.REQUIRES_MODIFICATION,
    ],
)
def test_get_approval_response_type_from_metadata(response_type):
    assert (
        get_approval_response_type_from_metadata({"approval_response_type": response_type.value})
        == response_type
    )


@pytest.mark.parametrize("metadata", [None, {}, {"comment": "hello"}])
def test_get_approval_response_type_from_metadata_missing(metadata):
    with pytest.raises(
        InvalidWorkflowResponseTypeError, match="Approval response type not found in metadata"
    ):
        get_approval_response_type_from_metadata(metadata)


def test_get_approval_response_type_from_metadata_invalid():
    with pytest.raises(
        InvalidWorkflowResponseTypeError, match="Approval response type is not a valid value"
    ):
        get_approval_response_type_from_metadata({"approval_response_type": "not-a-real-value"})


def test_validate_approval_response_type():
    approval_config = ApprovalConfig(
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        approval_state="pending_primary_approval",
        required_privileges=[Privilege.UPDATE_PROGRAM],
        allowed_approval_response_types={ApprovalResponseType.APPROVED},
    )

    # Allowed - does not raise
    validate_approval_response_type(ApprovalResponseType.APPROVED, approval_config)

    with pytest.raises(
        DisallowedApprovalResponseTypeError,
        match="Approval response type is not allowed for this approval configuration",
    ) as err:
        validate_approval_response_type(ApprovalResponseType.DECLINED, approval_config)

    assert err.value.allowed_approval_response_types == {ApprovalResponseType.APPROVED}

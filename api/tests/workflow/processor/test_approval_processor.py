import pytest

from src.constants.lookup_constants import (
    ApprovalResponseType,
    ApprovalType,
    Privilege,
    WorkflowType,
)
from src.workflow.workflow_errors import (
    DisallowedApprovalResponseTypeError,
    DuplicateApprovalError,
    InvalidWorkflowResponseTypeError,
)
from tests.db.models.factories import ProgramWorkflowFactory, WorkflowApprovalFactory
from tests.workflow.state_machine.test_state_machines import (
    ApprovalState,
    LimitedApprovalResponseState,
)
from tests.workflow.workflow_test_util import (
    create_approver,
    send_process_event,
    validate_approvals,
)


def build_workflow(program, state: str, workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW):
    return ProgramWorkflowFactory.create(
        workflow_type=workflow_type,
        current_workflow_state=state,
        program=program,
    )


def test_approval_accepted_simple(db_session, program, secondary_approver):
    workflow = build_workflow(program, ApprovalState.PENDING_SECONDARY_APPROVAL)

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_secondary_approval",
        workflow_id=workflow.workflow_id,
        user=secondary_approver,
        expected_state=ApprovalState.END,
        expected_is_active=False,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    validate_approvals(
        state_machine,
        [
            {
                "approving_user_id": secondary_approver.user_id,
                "approval_type": ApprovalType.SECONDARY_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
        ],
    )


def test_approval_declined(db_session, program, secondary_approver):
    workflow = build_workflow(program, ApprovalState.PENDING_SECONDARY_APPROVAL)

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_secondary_approval",
        workflow_id=workflow.workflow_id,
        user=secondary_approver,
        expected_state=ApprovalState.DECLINED,
        expected_is_active=False,
        approval_response_type=ApprovalResponseType.DECLINED,
    )

    validate_approvals(
        state_machine,
        [
            {
                "approving_user_id": secondary_approver.user_id,
                "approval_type": ApprovalType.SECONDARY_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.DECLINED,
            },
        ],
    )


def test_approval_requires_modification(db_session, program, secondary_approver):
    workflow = build_workflow(program, ApprovalState.PENDING_SECONDARY_APPROVAL)

    # add a prior approval that will be invalidated
    prior_approval = WorkflowApprovalFactory.create(
        workflow=workflow,
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        is_still_valid=True,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_secondary_approval",
        workflow_id=workflow.workflow_id,
        user=secondary_approver,
        expected_state=ApprovalState.START,
        approval_response_type=ApprovalResponseType.REQUIRES_MODIFICATION,
        comment="requires more info",
    )

    validate_approvals(
        state_machine,
        [
            {
                "approving_user_id": prior_approval.approving_user_id,
                "approval_type": prior_approval.approval_type,
                "is_still_valid": False,
                "approval_response_type": prior_approval.approval_response_type,
            },
            {
                "approving_user_id": secondary_approver.user_id,
                "approval_type": ApprovalType.SECONDARY_TEST_APPROVAL,
                "is_still_valid": False,
                "approval_response_type": ApprovalResponseType.REQUIRES_MODIFICATION,
                "comment": "requires more info",
            },
        ],
    )


def test_approval_accepted_with_prior_invalid_history(db_session, program, secondary_approver):
    workflow = build_workflow(program, ApprovalState.PENDING_SECONDARY_APPROVAL)

    prior_approval = WorkflowApprovalFactory.create(
        workflow=workflow,
        approving_user=secondary_approver,
        approval_type=ApprovalType.SECONDARY_TEST_APPROVAL,
        is_still_valid=False,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_secondary_approval",
        workflow_id=workflow.workflow_id,
        user=secondary_approver,
        expected_state=ApprovalState.END,
        expected_is_active=False,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    validate_approvals(
        state_machine,
        [
            prior_approval,
            {
                "approving_user_id": secondary_approver.user_id,
                "approval_type": ApprovalType.SECONDARY_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
        ],
    )


def test_approval_accepted_multiple_approvals_required(db_session, program, primary_approver):
    """The primary approval requires three approvals before the state moves on."""
    primary_approver2 = create_approver(
        db_session, program.grant_office, privileges=[Privilege.UPDATE_PROGRAM]
    )
    primary_approver3 = create_approver(
        db_session, program.grant_office, privileges=[Privilege.UPDATE_PROGRAM]
    )

    workflow = build_workflow(program, ApprovalState.PENDING_PRIMARY_APPROVAL)

    send_process_event(
        db_session=db_session,
        event_to_send="receive_primary_approval",
        workflow_id=workflow.workflow_id,
        user=primary_approver,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
        approval_response_type=ApprovalResponseType.APPROVED,
    )
    send_process_event(
        db_session=db_session,
        event_to_send="receive_primary_approval",
        workflow_id=workflow.workflow_id,
        user=primary_approver2,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_primary_approval",
        workflow_id=workflow.workflow_id,
        user=primary_approver3,
        expected_state=ApprovalState.END,
        expected_is_active=False,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    validate_approvals(
        state_machine,
        [
            {
                "approving_user_id": primary_approver.user_id,
                "approval_type": ApprovalType.BASIC_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
            {
                "approving_user_id": primary_approver2.user_id,
                "approval_type": ApprovalType.BASIC_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
            {
                "approving_user_id": primary_approver3.user_id,
                "approval_type": ApprovalType.BASIC_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
        ],
    )


def test_approval_user_already_approved(db_session, program, primary_approver):
    workflow = build_workflow(program, ApprovalState.PENDING_PRIMARY_APPROVAL)

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_primary_approval",
        workflow_id=workflow.workflow_id,
        user=primary_approver,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    # Try again and it will error
    with pytest.raises(DuplicateApprovalError, match="User already has an active approval"):
        send_process_event(
            db_session=db_session,
            event_to_send="receive_primary_approval",
            workflow_id=workflow.workflow_id,
            user=primary_approver,
            expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
            approval_response_type=ApprovalResponseType.APPROVED,
        )

    # only the first approval is recorded
    validate_approvals(
        state_machine,
        [
            {
                "approving_user_id": primary_approver.user_id,
                "approval_type": ApprovalType.BASIC_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
        ],
    )


def test_approval_user_has_different_approval(db_session, program, secondary_approver):
    """Verify that a user is capable of doing different approvals"""
    workflow = build_workflow(program, ApprovalState.PENDING_SECONDARY_APPROVAL)

    # Add a prior approval of a different type
    prior_approval = WorkflowApprovalFactory.create(
        workflow=workflow,
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        approving_user=secondary_approver,
    )

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_secondary_approval",
        workflow_id=workflow.workflow_id,
        user=secondary_approver,
        expected_state=ApprovalState.END,
        expected_is_active=False,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    validate_approvals(
        state_machine,
        [
            prior_approval,
            {
                "approving_user_id": secondary_approver.user_id,
                "approval_type": ApprovalType.SECONDARY_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
        ],
    )


def test_approval_approve_then_decline(db_session, program, primary_approver):
    primary_approver2 = create_approver(
        db_session, program.grant_office, privileges=[Privilege.UPDATE_PROGRAM]
    )

    workflow = build_workflow(program, ApprovalState.PENDING_PRIMARY_APPROVAL)

    send_process_event(
        db_session=db_session,
        event_to_send="receive_primary_approval",
        workflow_id=workflow.workflow_id,
        user=primary_approver,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
        approval_response_type=ApprovalResponseType.APPROVED,
    )
    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_primary_approval",
        workflow_id=workflow.workflow_id,
        user=primary_approver2,
        expected_state=ApprovalState.DECLINED,
        expected_is_active=False,
        approval_response_type=ApprovalResponseType.DECLINED,
    )

    validate_approvals(
        state_machine,
        [
            {
                "approving_user_id": primary_approver.user_id,
                "approval_type": ApprovalType.BASIC_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
            {
                "approving_user_id": primary_approver2.user_id,
                "approval_type": ApprovalType.BASIC_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.DECLINED,
            },
        ],
    )


def test_approval_invalid_response_type(db_session, program, secondary_approver):
    workflow = build_workflow(program, ApprovalState.PENDING_SECONDARY_APPROVAL)

    with pytest.raises(
        InvalidWorkflowResponseTypeError, match="Approval response type is not a valid value"
    ):
        send_process_event(
            db_session=db_session,
            event_to_send="receive_secondary_approval",
            workflow_id=workflow.workflow_id,
            user=secondary_approver,
            expected_state=ApprovalState.PENDING_SECONDARY_APPROVAL,
            approval_response_type="not-a-valid-type",
        )

    assert len(workflow.workflow_approvals) == 0


def test_approval_null_response_type(db_session, program, secondary_approver):
    workflow = build_workflow(program, ApprovalState.PENDING_SECONDARY_APPROVAL)

    with pytest.raises(
        InvalidWorkflowResponseTypeError, match="Approval response type not found in metadata"
    ):
        send_process_event(
            db_session=db_session,
            event_to_send="receive_secondary_approval",
            workflow_id=workflow.workflow_id,
            user=secondary_approver,
            expected_state=ApprovalState.PENDING_SECONDARY_APPROVAL,
            # no type passed in
        )

    assert len(workflow.workflow_approvals) == 0


####################
# Limited approval response types
####################


def test_limited_approval_response_allowed_type(db_session, program, primary_approver):
    """APPROVED is allowed for the primary approval"""
    workflow = build_workflow(
        program,
        LimitedApprovalResponseState.PENDING_PRIMARY_APPROVAL,
        workflow_type=WorkflowType.LIMITED_APPROVAL_TEST_WORKFLOW,
    )

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_primary_approval",
        workflow_id=workflow.workflow_id,
        user=primary_approver,
        expected_state=LimitedApprovalResponseState.END,
        expected_is_active=False,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    validate_approvals(
        state_machine,
        [
            {
                "approving_user_id": primary_approver.user_id,
                "approval_type": ApprovalType.BASIC_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
        ],
    )


def test_limited_approval_response_requires_modification_allowed(
    db_session, program, primary_approver
):
    """REQUIRES_MODIFICATION is allowed for the primary approval"""
    workflow = build_workflow(
        program,
        LimitedApprovalResponseState.PENDING_PRIMARY_APPROVAL,
        workflow_type=WorkflowType.LIMITED_APPROVAL_TEST_WORKFLOW,
    )

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_primary_approval",
        workflow_id=workflow.workflow_id,
        user=primary_approver,
        expected_state=LimitedApprovalResponseState.START,
        approval_response_type=ApprovalResponseType.REQUIRES_MODIFICATION,
    )

    validate_approvals(
        state_machine,
        [
            {
                "approving_user_id": primary_approver.user_id,
                "approval_type": ApprovalType.BASIC_TEST_APPROVAL,
                "is_still_valid": False,
                "approval_response_type": ApprovalResponseType.REQUIRES_MODIFICATION,
            },
        ],
    )


def test_limited_approval_response_disallowed_type_primary(db_session, program, primary_approver):
    """DECLINED is not allowed for the primary approval"""
    workflow = build_workflow(
        program,
        LimitedApprovalResponseState.PENDING_PRIMARY_APPROVAL,
        workflow_type=WorkflowType.LIMITED_APPROVAL_TEST_WORKFLOW,
    )

    with pytest.raises(
        DisallowedApprovalResponseTypeError,
        match="Approval response type is not allowed for this approval configuration",
    ):
        send_process_event(
            db_session=db_session,
            event_to_send="receive_primary_approval",
            workflow_id=workflow.workflow_id,
            user=primary_approver,
            expected_state=LimitedApprovalResponseState.PENDING_PRIMARY_APPROVAL,
            approval_response_type=ApprovalResponseType.DECLINED,
        )

    # No approvals should be recorded
    assert len(workflow.workflow_approvals) == 0


def test_limited_approval_response_secondary_only_approved(db_session, program, secondary_approver):
    """Only APPROVED is allowed for the secondary approval"""
    workflow = build_workflow(
        program,
        LimitedApprovalResponseState.PENDING_SECONDARY_APPROVAL,
        workflow_type=WorkflowType.LIMITED_APPROVAL_TEST_WORKFLOW,
    )

    state_machine = send_process_event(
        db_session=db_session,
        event_to_send="receive_secondary_approval",
        workflow_id=workflow.workflow_id,
        user=secondary_approver,
        expected_state=LimitedApprovalResponseState.END,
        expected_is_active=False,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    validate_approvals(
        state_machine,
        [
            {
                "approving_user_id": secondary_approver.user_id,
                "approval_type": ApprovalType.SECONDARY_TEST_APPROVAL,
                "is_still_valid": True,
                "approval_response_type": ApprovalResponseType.APPROVED,
            },
        ],
    )


@pytest.mark.parametrize(
    "approval_response_type",
    [ApprovalResponseType.DECLINED, ApprovalResponseType.REQUIRES_MODIFICATION],
)
def test_limited_approval_response_secondary_disallowed(
    db_session, program, secondary_approver, approval_response_type
):
    """Neither DECLINED nor REQUIRES_MODIFICATION is allowed for the secondary approval"""
    workflow = build_workflow(
        program,
        LimitedApprovalResponseState.PENDING_SECONDARY_APPROVAL,
        workflow_type=WorkflowType.LIMITED_APPROVAL_TEST_WORKFLOW,
    )

    with pytest.raises(
        DisallowedApprovalResponseTypeError,
        match="Approval response type is not allowed for this approval configuration",
    ):
        send_process_event(
            db_session=db_session,
            event_to_send="receive_secondary_approval",
            workflow_id=workflow.workflow_id,
            user=secondary_approver,
            expected_state=LimitedApprovalResponseState.PENDING_SECONDARY_APPROVAL,
            approval_response_type=approval_response_type,
        )

    # No approvals should be recorded
    assert len(workflow.workflow_approvals) == 0

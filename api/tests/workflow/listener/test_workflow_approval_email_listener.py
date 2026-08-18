import logging

from src.constants.lookup_constants import ApprovalResponseType, Privilege, WorkflowType
from src.db.models.user_models import User
from src.db.models.workflow_models import Workflow
from tests.db.models.factories import ProgramWorkflowFactory, UserFactory
from tests.test_utils.auth_test_utils import setup_user_with_roles
from tests.workflow.state_machine.test_state_machines import ApprovalState
from tests.workflow.workflow_test_util import create_approver, send_process_event


def verify_email(
    sent_message,
    user: User,
    workflow: Workflow,
    expected_state: ApprovalState,
    expected_privilege: Privilege,
) -> None:
    """Verify a sent email message from the moto SES backend."""
    assert user.email in sent_message.destinations["ToAddresses"]

    assert sent_message.subject == "Approval required for 'Approval Test Workflow'"

    body = sent_message.body

    assert (
        f"An approval is required for a Approval Test Workflow that is currently in state '{expected_state}' from a user with the following privilege(s): {expected_privilege}"
        in body
    )
    assert f"ID: {workflow.workflow_id}" in body
    assert f"Resource: program ({workflow.resource_id})" in body


def build_workflow(program, state: str) -> Workflow:
    return ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW,
        current_workflow_state=state,
        program=program,
    )


def test_approval_email_listener_moving_into_secondary_approval_state(
    db_session, program, secondary_approver, ses_client, get_sent_emails
):
    """Verify that when we first enter an approval state, an email is sent"""

    # A random user that caused the prior event
    user = UserFactory.create()

    workflow = build_workflow(program, ApprovalState.MIDDLE)

    send_process_event(
        db_session=db_session,
        event_to_send="middle_to_secondary_approval",
        workflow_id=workflow.workflow_id,
        user=user,
        expected_state=ApprovalState.PENDING_SECONDARY_APPROVAL,
    )

    emails = get_sent_emails()
    assert len(emails) == 1
    verify_email(
        emails[0],
        user=secondary_approver,
        workflow=workflow,
        expected_state=ApprovalState.PENDING_SECONDARY_APPROVAL,
        expected_privilege=Privilege.VIEW_PROGRAM,
    )


def test_approval_email_listener_moving_into_primary_approval_state(
    db_session, program, primary_approver, ses_client, get_sent_emails
):
    user = UserFactory.create()

    workflow = build_workflow(program, ApprovalState.MIDDLE)

    send_process_event(
        db_session=db_session,
        event_to_send="middle_to_primary_approval",
        workflow_id=workflow.workflow_id,
        user=user,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
    )

    emails = get_sent_emails()
    assert len(emails) == 1
    verify_email(
        emails[0],
        user=primary_approver,
        workflow=workflow,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
        expected_privilege=Privilege.UPDATE_PROGRAM,
    )


def test_approval_email_listener_multiple_users_can_approve(
    db_session, program, primary_approver, ses_client, get_sent_emails
):
    # A few more users that could do the approval
    primary_approver2 = create_approver(
        db_session, program.grant_office, privileges=[Privilege.UPDATE_PROGRAM]
    )
    primary_approver3 = create_approver(
        db_session, program.grant_office, privileges=[Privilege.UPDATE_PROGRAM]
    )

    # This user's privilege is inherited from the partner above the program, which
    # counts the same as one held on the offices.
    inherited_approver = create_approver(
        db_session, program.partner, privileges=[Privilege.UPDATE_PROGRAM]
    )

    # This user has a role in scope, but not the privilege the approval needs
    create_approver(db_session, program.program_office, privileges=[Privilege.VIEW_PROGRAM])

    # A random user that caused the prior event
    user = UserFactory.create()

    workflow = build_workflow(program, ApprovalState.MIDDLE)

    send_process_event(
        db_session=db_session,
        event_to_send="middle_to_primary_approval",
        workflow_id=workflow.workflow_id,
        user=user,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
    )

    emails = get_sent_emails()

    # The approver query doesn't order its rows, so match recipients rather than
    # asserting an order the engine never promised.
    approvers = [primary_approver, primary_approver2, primary_approver3, inherited_approver]

    assert len(emails) == len(approvers)
    emails_by_address = {email.destinations["ToAddresses"][0]: email for email in emails}
    assert set(emails_by_address) == {approver.email for approver in approvers}

    for approver in approvers:
        verify_email(
            emails_by_address[approver.email],
            user=approver,
            workflow=workflow,
            expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
            expected_privilege=Privilege.UPDATE_PROGRAM,
        )


def test_approval_email_listener_user_without_email_not_notified(
    db_session, program, ses_client, get_sent_emails, caplog
):
    """A user with no login.gov login has no email address, so gets no notification."""
    # Letting setup_user_with_roles create the user leaves it without an external
    # user record, and therefore without an email. The role goes on the grant office so
    # the user is a genuine approver being dropped for the missing address, rather than
    # one the lookup never saw.
    setup_user_with_roles(
        db_session, resources=[program.grant_office], privileges=[Privilege.UPDATE_PROGRAM]
    )

    user = UserFactory.create()
    workflow = build_workflow(program, ApprovalState.MIDDLE)

    send_process_event(
        db_session=db_session,
        event_to_send="middle_to_primary_approval",
        workflow_id=workflow.workflow_id,
        user=user,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
    )

    assert len(get_sent_emails()) == 0
    assert caplog.messages.count("No users can do approval - cannot send email") == 1


def test_approval_email_listener_staying_in_approval_state_no_email(
    db_session, program, primary_approver, caplog, ses_client, get_sent_emails
):
    """Verify that if a workflow re-enters an approval state that it's already in, no email is sent"""

    caplog.set_level(logging.DEBUG)

    # This state requires multiple approvals, we'll do 2 to show
    # that no emails get sent as long as it stays in the state.
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

    send_process_event(
        db_session=db_session,
        event_to_send="receive_primary_approval",
        workflow_id=workflow.workflow_id,
        user=primary_approver2,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
        approval_response_type=ApprovalResponseType.APPROVED,
    )

    assert len(get_sent_emails()) == 0

    # Verify using the logs that this was the path it went down
    # and that it happened four times (each event moves it twice due to checking the count of approvals)
    assert caplog.messages.count("State is not changing, not sending approval emails.") == 4


def test_approval_email_listener_non_approval_states(
    db_session, program, caplog, ses_client, get_sent_emails
):
    """Test that if a state isn't an approval state, no emails are sent"""

    caplog.set_level(logging.DEBUG)

    user = UserFactory.create()

    workflow = build_workflow(program, ApprovalState.START)

    # Send this from START to MIDDLE to END
    send_process_event(
        db_session=db_session,
        event_to_send="start_workflow",
        workflow_id=workflow.workflow_id,
        user=user,
        expected_state=ApprovalState.MIDDLE,
    )

    send_process_event(
        db_session=db_session,
        event_to_send="middle_to_end",
        workflow_id=workflow.workflow_id,
        user=user,
        expected_state=ApprovalState.END,
        expected_is_active=False,
    )

    assert len(get_sent_emails()) == 0

    # Verify using the logs that this was the path it went down
    assert (
        caplog.messages.count("State does not have approval, no email notification required") == 2
    )


def test_approval_email_listener_no_users(db_session, program, caplog, ses_client, get_sent_emails):
    """Verify behavior if no users have the privilege"""

    # A random user that caused the prior event
    user = UserFactory.create()

    workflow = build_workflow(program, ApprovalState.MIDDLE)

    send_process_event(
        db_session=db_session,
        event_to_send="middle_to_primary_approval",
        workflow_id=workflow.workflow_id,
        user=user,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
    )

    assert len(get_sent_emails()) == 0

    assert caplog.messages.count("No users can do approval - cannot send email") == 1


def test_approval_email_listener_inherited_privilege_holder_notified(
    db_session, program, inherited_privilege_user, ses_client, get_sent_emails
):
    """A user whose approval privilege is inherited from a parent resource is emailed.

    The privilege here comes from the partner above the program rather than from the
    program's own offices, and approvals reach as far as the authorization hierarchy does.
    """
    user = UserFactory.create()

    workflow = build_workflow(program, ApprovalState.MIDDLE)

    send_process_event(
        db_session=db_session,
        event_to_send="middle_to_primary_approval",
        workflow_id=workflow.workflow_id,
        user=user,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
    )

    emails = get_sent_emails()
    assert len(emails) == 1
    verify_email(
        emails[0],
        user=inherited_privilege_user,
        workflow=workflow,
        expected_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
        expected_privilege=Privilege.UPDATE_PROGRAM,
    )

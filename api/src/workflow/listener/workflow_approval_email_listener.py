import logging

from statemachine.event_data import EventData

from src.adapters import db
from src.db.models.user_models import User
from src.workflow.event.state_machine_event import StateMachineEvent
from src.workflow.service.approval_service import get_approver_query
from src.workflow.util.workflow_util import send_workflow_email
from src.workflow.workflow_errors import UnexpectedStateError

logger = logging.getLogger(__name__)

APPROVAL_EMAIL_SUBJECT_TEMPLATE = "Approval required for '{workflow_type}'"

# Note that any newlines (\n) here will be replaced with <br/> below
# for the purposes of email formatting.
#
# The resource is identified by type and ID rather than a name - resolving a
# display name would mean a per-resource-type lookup in the listener, and there is
# no grants management frontend to link to yet either.
APPROVAL_EMAIL_TEMPLATE = """An approval is required for a {workflow_type} that is currently in state '{current_workflow_state}' from a user with the following privilege(s): {privileges}.

ID: {workflow_id}
Resource: {resource_type} ({resource_id})"""


class WorkflowApprovalEmailListener:
    """
    Listener for state machine transitions that automatically
    sends emails to approval users whenever a workflow
    enters into a state that requires approval.
    """

    def __init__(self, db_session: db.Session):
        """
        Initialize the approval email listener.
        """
        self.db_session = db_session

    def on_enter_state(self, state_machine_event: StateMachineEvent, event_data: EventData) -> None:
        """
        Listen for events when a workflow enters a state that is also an approval.
        """
        # Target shouldn't be None with how we define state machines
        # but the library allows for it, so we have to be careful
        if event_data.target is None:
            raise UnexpectedStateError("Workflow transition is missing a target state")
        target_state = event_data.target.value
        log_extra = state_machine_event.get_log_extra() | {
            "source_state": event_data.source.value,
            "target_state": target_state,
        }

        approval_config = state_machine_event.config.state_approval_mapping.get(target_state, None)
        if approval_config is None:
            logger.debug(
                "State does not have approval, no email notification required", extra=log_extra
            )
            return

        # If the state machine's state is NOT changing as part of this
        # then we don't want to do anything. We only want to send
        # emails when first entering the state.
        if event_data.source == target_state:
            logger.debug("State is not changing, not sending approval emails.", extra=log_extra)
            return

        # The same query that decides whether a user may approve, so nobody is emailed
        # an approval request they'd be turned away from (or silently left out of one
        # they could act on).
        stmt = get_approver_query(self.db_session, state_machine_event.workflow, approval_config)
        # A user with no login.gov link comes back with a null email - there's nowhere
        # to send their notification, so drop them here rather than in the query.
        users: list[User] = [
            user for user in self.db_session.execute(stmt).scalars() if user.email is not None
        ]
        logger.info(
            "Fetched users that could potentially do approval",
            extra=log_extra | {"user_count": len(users), "target_state": target_state},
        )

        if len(users) == 0:
            logger.warning("No users can do approval - cannot send email", extra=log_extra)
            return

        subject = APPROVAL_EMAIL_SUBJECT_TEMPLATE.format(
            workflow_type=state_machine_event.workflow.workflow_type.get_human_friendly_text()
        )

        approval_message = APPROVAL_EMAIL_TEMPLATE.format(
            workflow_id=state_machine_event.workflow.workflow_id,
            current_workflow_state=state_machine_event.workflow.current_workflow_state,
            workflow_type=state_machine_event.workflow.workflow_type.get_human_friendly_text(),
            resource_type=state_machine_event.workflow.resource.resource_type,
            resource_id=state_machine_event.workflow.resource_id,
            privileges=",".join(approval_config.required_privileges),
        ).replace("\n", "<br/>")

        for user in users:
            send_workflow_email(
                state_machine_event=state_machine_event,
                user=user,
                subject=subject,
                message=approval_message,
            )

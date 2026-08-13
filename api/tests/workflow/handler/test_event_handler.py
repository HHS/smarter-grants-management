import uuid

import pytest

from src.constants.lookup_constants import MgmtWorkflowType
from src.workflow.handler.event_handler import EventHandler
from src.workflow.state_machine.prototype_state_machine import PrototypeState, PrototypeStateMachine
from src.workflow.workflow_errors import (
    ConcurrentWorkflowError,
    EntityNotFound,
    InactiveWorkflowError,
    InvalidEntityForWorkflow,
    InvalidEventError,
    InvalidWorkflowTypeError,
    UnexpectedStateError,
    UserDoesNotExist,
    WorkflowDoesNotExistError,
)
from tests.db.models.factories import MgmtUserFactory, PartnerFactory, ProgramWorkflowFactory
from tests.workflow.state_machine.test_state_machines import BasicState, BasicTestStateMachine
from tests.workflow.workflow_test_util import (
    build_process_workflow_event,
    build_start_workflow_event,
)

####################
# Starting a workflow
####################


def test_start_workflow_event(db_session, enable_factory_create, program):
    user = MgmtUserFactory.create()

    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
    )

    state_machine = EventHandler(db_session, sqs_container).process()

    assert state_machine.workflow.current_workflow_state == BasicState.MIDDLE
    assert state_machine.workflow.is_active is True
    # The workflow points at the entity solely through its resource
    assert state_machine.workflow.mgmt_resource_id == program.get_resource_id()
    assert state_machine.workflow.workflow_type == MgmtWorkflowType.BASIC_TEST_WORKFLOW

    # The history event is linked back to the workflow it turned out to be for
    assert sqs_container.history_event.workflow is state_machine.workflow


def test_start_workflow_event_records_transition_details(
    db_session, enable_factory_create, program
):
    """The state machine event carries the resolved user, workflow, and class through."""
    user = MgmtUserFactory.create()

    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
    )

    state_machine = EventHandler(db_session, sqs_container).process()

    assert len(state_machine.transition_history) == 1

    state_machine_event = state_machine.transition_history[0]
    assert state_machine_event.event_to_send == "start_workflow"
    assert state_machine_event.acting_user.mgmt_user_id == user.mgmt_user_id
    assert state_machine_event.workflow is state_machine.workflow
    assert state_machine_event.state_machine_cls is BasicTestStateMachine


def test_start_workflow_event_missing_start_context(db_session, enable_factory_create, program):
    user = MgmtUserFactory.create()

    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
        exclude_start_workflow_context=True,
    )

    with pytest.raises(InvalidEventError, match="Start workflow event cannot have null context"):
        EventHandler(db_session, sqs_container).process()


def test_start_workflow_event_invalid_workflow_type(db_session, enable_factory_create, program):
    user = MgmtUserFactory.create()

    sqs_container = build_start_workflow_event(
        # We'll override this below
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
    )
    # Pydantic doesn't validate on assignment, so change it to something invalid here
    sqs_container.workflow_event.start_workflow_context.workflow_type = "not-a-valid-workflow-type"

    with pytest.raises(
        InvalidWorkflowTypeError, match="Workflow event does not map to an actual state machine"
    ):
        EventHandler(db_session, sqs_container).process()


def test_start_workflow_event_resource_does_not_exist(db_session, enable_factory_create, program):
    user = MgmtUserFactory.create()

    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
    )
    sqs_container.workflow_event.start_workflow_context.mgmt_resource_id = uuid.uuid4()

    with pytest.raises(EntityNotFound, match="Resource not found"):
        EventHandler(db_session, sqs_container).process()


def test_start_workflow_event_wrong_resource_type(db_session, enable_factory_create):
    """The workflow's persistence model declares programs, so a partner is rejected."""
    user = MgmtUserFactory.create()
    partner = PartnerFactory.create()

    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=partner,
    )

    with pytest.raises(
        InvalidEntityForWorkflow, match="Resource type does not match workflow configuration"
    ):
        EventHandler(db_session, sqs_container).process()


def test_start_workflow_event_missing_user(db_session, enable_factory_create, program):
    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=None,  # A random ID will be added
        entity=program,
    )

    with pytest.raises(UserDoesNotExist, match="User does not exist"):
        EventHandler(db_session, sqs_container).process()


####################
# Processing an existing workflow
####################


def test_process_workflow_event(db_session, enable_factory_create):
    user = MgmtUserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=BasicState.MIDDLE,
    )

    sqs_container = build_process_workflow_event(
        workflow.mgmt_workflow_id, user=user, event_to_send="middle_to_end"
    )

    state_machine = EventHandler(db_session, sqs_container).process()

    assert isinstance(state_machine, BasicTestStateMachine)
    assert state_machine.workflow.current_workflow_state == BasicState.END
    # Reaching a final state deactivates the workflow
    assert state_machine.workflow.is_active is False


def test_process_workflow_event_resolves_state_machine_from_the_workflow(
    db_session, enable_factory_create
):
    """A process event doesn't carry a workflow type - it comes off the stored workflow."""
    user = MgmtUserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    sqs_container = build_process_workflow_event(
        workflow.mgmt_workflow_id, user=user, event_to_send="complete"
    )

    state_machine = EventHandler(db_session, sqs_container).process()

    # The prototype was resolved off the workflow row, not off the event
    assert isinstance(state_machine, PrototypeStateMachine)
    # `complete` moves to FINALIZING and the state machine sends `finalize` itself,
    # which lands on a final state and deactivates the workflow.
    assert state_machine.workflow.current_workflow_state == PrototypeState.END
    assert state_machine.workflow.is_active is False


def test_process_workflow_event_missing_process_context(db_session, enable_factory_create):
    user = MgmtUserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=BasicState.MIDDLE,
    )

    sqs_container = build_process_workflow_event(
        workflow.mgmt_workflow_id,
        user=user,
        event_to_send="middle_to_end",
        exclude_process_workflow_context=True,
    )

    with pytest.raises(
        InvalidEventError, match="Process workflow event has a null process workflow context"
    ):
        EventHandler(db_session, sqs_container).process()


def test_process_workflow_event_missing_user(db_session, enable_factory_create):
    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=BasicState.MIDDLE,
    )

    sqs_container = build_process_workflow_event(
        workflow.mgmt_workflow_id, user=None, event_to_send="middle_to_end"
    )
    with pytest.raises(UserDoesNotExist, match="User does not exist"):
        EventHandler(db_session, sqs_container).process()


def test_process_workflow_event_workflow_does_not_exist(db_session, enable_factory_create):
    user = MgmtUserFactory.create()

    sqs_container = build_process_workflow_event(
        mgmt_workflow_id=uuid.uuid4(), user=user, event_to_send="middle_to_end"
    )

    with pytest.raises(WorkflowDoesNotExistError, match="Workflow does not exist"):
        EventHandler(db_session, sqs_container).process()


def test_process_workflow_event_invalid_event(db_session, enable_factory_create):
    user = MgmtUserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=BasicState.MIDDLE,
    )

    sqs_container = build_process_workflow_event(
        workflow.mgmt_workflow_id, user=user, event_to_send="not-a-real-event"
    )
    with pytest.raises(InvalidEventError, match="Event is not valid for workflow"):
        EventHandler(db_session, sqs_container).process()


def test_process_workflow_event_invalid_event_for_current_state(db_session, enable_factory_create):
    user = MgmtUserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=BasicState.MIDDLE,
    )

    # start_workflow is valid, just not for the current state
    sqs_container = build_process_workflow_event(
        workflow.mgmt_workflow_id, user=user, event_to_send="start_workflow"
    )
    with pytest.raises(InvalidEventError, match="Event is not valid for workflow"):
        EventHandler(db_session, sqs_container).process()


def test_process_workflow_event_invalid_current_state(db_session, enable_factory_create):
    user = MgmtUserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state="not-a-valid-state",
    )

    sqs_container = build_process_workflow_event(
        workflow.mgmt_workflow_id, user=user, event_to_send="middle_to_end"
    )
    with pytest.raises(UnexpectedStateError, match="Workflow record has an unexpected state"):
        EventHandler(db_session, sqs_container).process()


def test_process_workflow_is_already_at_end(db_session, enable_factory_create):
    user = MgmtUserFactory.create()

    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        current_workflow_state=BasicState.END,
        is_active=False,
    )

    sqs_container = build_process_workflow_event(
        workflow.mgmt_workflow_id, user=user, event_to_send="middle_to_end"
    )
    with pytest.raises(
        InactiveWorkflowError, match="Workflow is not active - cannot receive events"
    ):
        EventHandler(db_session, sqs_container).process()


####################
# Concurrent workflows
####################


def test_start_workflow_event_concurrent_workflow_blocked(
    db_session, enable_factory_create, program
):
    """Starting a workflow should fail if an active workflow of the same type already exists
    for the resource and the config disallows concurrent workflows."""
    user = MgmtUserFactory.create()

    # Create an existing active workflow for the same resource and workflow type
    ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        program=program,
        is_active=True,
    )

    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
    )

    with pytest.raises(
        ConcurrentWorkflowError,
        match="An active workflow of this type already exists for this resource",
    ):
        EventHandler(db_session, sqs_container).process()


def test_start_workflow_event_concurrent_workflow_allowed_when_inactive(
    db_session, enable_factory_create, program
):
    """Starting a workflow should succeed if an existing workflow is inactive
    even when the config disallows concurrent workflows."""
    user = MgmtUserFactory.create()

    # Create an existing INACTIVE workflow for the same resource and workflow type
    ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        program=program,
        is_active=False,
    )

    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
    )

    state_machine = EventHandler(db_session, sqs_container).process()

    assert state_machine.workflow.is_active is True


def test_start_workflow_event_concurrent_workflow_allowed_by_config(
    db_session, enable_factory_create, program
):
    """The prototype allows concurrent workflows, so an active one doesn't block a second."""
    user = MgmtUserFactory.create()

    ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.PROTOTYPE_WORKFLOW,
        program=program,
        is_active=True,
    )

    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.PROTOTYPE_WORKFLOW,
        user=user,
        entity=program,
    )

    state_machine = EventHandler(db_session, sqs_container).process()

    assert isinstance(state_machine, PrototypeStateMachine)
    assert state_machine.workflow.is_active is True

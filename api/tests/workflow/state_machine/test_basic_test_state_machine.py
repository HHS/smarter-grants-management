"""Tests for the test-only state machine that the engine tests run against.

These cover the state machine itself, so a change to its shape shows up here rather
than as a confusing failure somewhere in the engine tests that depend on it.
"""

from src.constants.lookup_constants import MgmtResourceType, MgmtWorkflowType
from src.workflow.handler.event_handler import EventHandler
from src.workflow.state_persistence.program_persistence_model import ProgramPersistenceModel
from tests.db.models.factories import MgmtUserFactory
from tests.workflow.state_machine.test_state_machines import (
    BasicState,
    BasicTestStateMachine,
    basic_test_workflow_config,
)
from tests.workflow.workflow_test_util import build_start_workflow_event, send_process_event


def test_basic_test_workflow_config():
    assert basic_test_workflow_config.workflow_type == MgmtWorkflowType.BASIC_TEST_WORKFLOW
    assert basic_test_workflow_config.persistence_model_cls is ProgramPersistenceModel
    assert basic_test_workflow_config.resource_type == MgmtResourceType.PROGRAM
    # Disallowed here so the engine's concurrency guard has something to test against
    assert basic_test_workflow_config.allow_concurrent_workflow_for_resource is False


def test_basic_test_state_machine_shape():
    assert BasicTestStateMachine.initial_state.value == BasicState.START
    assert BasicTestStateMachine.get_valid_events() == {"start_workflow", "middle_to_end"}
    assert BasicTestStateMachine.get_valid_states() == [
        BasicState.START,
        BasicState.MIDDLE,
        BasicState.END,
    ]

    final_states = [state.value for state in BasicTestStateMachine.states if state.final]
    assert final_states == [BasicState.END]


def test_basic_test_workflow_runs_start_to_finish(db_session, enable_factory_create, program):
    """The happy path: a workflow starts, advances, and deactivates on reaching the end."""
    user = MgmtUserFactory.create()

    sqs_container = build_start_workflow_event(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        user=user,
        entity=program,
    )
    state_machine = EventHandler(db_session, sqs_container).process()

    assert state_machine.workflow.current_workflow_state == BasicState.MIDDLE
    assert state_machine.workflow.is_active is True

    state_machine = send_process_event(
        db_session,
        event_to_send="middle_to_end",
        mgmt_workflow_id=state_machine.workflow.mgmt_workflow_id,
        user=user,
        expected_state=BasicState.END,
        expected_is_active=False,
    )

    # One transition per event, each recorded on the state machine it ran against
    assert len(state_machine.transition_history) == 1

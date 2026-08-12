"""
This file contains state machines that only exist for our unit tests.

Testing core engine logic against a state machine defined here rather than against
the prototype (or, later, a real workflow) means these tests don't have to change
every time a real workflow does.
"""

from enum import StrEnum
from typing import Any

from statemachine import Event
from statemachine.states import States

from src.constants.lookup_constants import MgmtWorkflowType
from src.workflow.base_state_machine import BaseStateMachine
from src.workflow.event.state_machine_event import StateMachineEvent
from src.workflow.registry.workflow_registry import WorkflowRegistry
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel
from src.workflow.state_persistence.program_persistence_model import ProgramPersistenceModel
from src.workflow.workflow_config import WorkflowConfig

#########################
# Basic State Machine
#########################
# A minimal start -> middle -> end workflow for exercising core engine behaviour.


class BasicState(StrEnum):
    START = "start"
    MIDDLE = "middle"
    END = "end"


basic_test_workflow_config = WorkflowConfig(
    workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
    persistence_model_cls=ProgramPersistenceModel,
    # Concurrent workflows are disallowed here so the engine's concurrency guard has a
    # registered workflow to test against. The prototype covers the allowed case, which
    # is the engine default.
    allow_concurrent_workflow_for_resource=False,
)


@WorkflowRegistry.register_workflow(basic_test_workflow_config)
class BasicTestStateMachine(BaseStateMachine):

    states = States.from_enum(
        BasicState,
        initial=BasicState.START,
        final=[BasicState.END],
    )

    ### Events + transitions
    start_workflow = Event(
        states.START.to(states.MIDDLE),
    )

    middle_to_end = Event(
        states.MIDDLE.to(states.END),
    )

    def __init__(self, model: BaseStatePersistenceModel, **kwargs: Any):
        super().__init__(model=model, **kwargs)

        # For testing purposes, store the transition events.
        self.transition_history: list[StateMachineEvent] = []

    def on_transition(self, state_machine_event: StateMachineEvent) -> None:
        self.transition_history.append(state_machine_event)

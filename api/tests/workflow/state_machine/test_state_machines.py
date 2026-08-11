"""
This file contains state machines that only exist for our unit tests.

The prototype state machine covers most of what the engine tests need, so this
file is deliberately thin - it holds the machines that need configuration the
prototype doesn't have (and shouldn't grow one just to be testable).
"""

from enum import StrEnum
from typing import Any

from statemachine import Event
from statemachine.states import States

from src.constants.lookup_constants import MgmtResourceType, MgmtWorkflowType
from src.workflow.base_state_machine import BaseStateMachine
from src.workflow.event.state_machine_event import StateMachineEvent
from src.workflow.registry.workflow_registry import WorkflowRegistry
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel
from src.workflow.workflow_config import WorkflowConfig

#########################
# No Concurrent State Machine
#########################
# For testing that concurrent workflows for the same
# resource are disallowed when configured. The prototype
# allows them, so this needs its own config.


class NoConcurrentState(StrEnum):
    START = "start"
    MIDDLE = "middle"
    END = "end"


no_concurrent_test_workflow_config = WorkflowConfig(
    workflow_type=MgmtWorkflowType.NO_CONCURRENT_TEST_WORKFLOW,
    persistence_model_cls=BaseStatePersistenceModel,
    resource_type=MgmtResourceType.PROGRAM,
    allow_concurrent_workflow_for_resource=False,
)


@WorkflowRegistry.register_workflow(no_concurrent_test_workflow_config)
class NoConcurrentTestStateMachine(BaseStateMachine):

    states = States.from_enum(
        NoConcurrentState,
        initial=NoConcurrentState.START,
        final=[NoConcurrentState.END],
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

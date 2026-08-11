from enum import StrEnum

from statemachine import Event
from statemachine.states import States

from src.constants.lookup_constants import MgmtResourceType, MgmtWorkflowType
from src.workflow.base_state_machine import BaseStateMachine
from src.workflow.registry.workflow_registry import WorkflowRegistry
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel
from src.workflow.workflow_config import WorkflowConfig


class PrototypeState(StrEnum):
    START = "start"
    IN_PROGRESS = "in_progress"

    # A transient state that exists only to demonstrate an automatic follow-on
    # transition - the engine sends `finalize` itself the moment `complete` lands.
    FINALIZING = "finalizing"

    # End State
    END = "end"


prototype_state_machine_config = WorkflowConfig(
    workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
    # Nothing about this workflow needs to touch the underlying entity, so the base
    # persistence model (which only writes state/is_active back to mgmt_workflow) is
    # all it needs. Real mgmt workflows will subclass it as their domains land.
    persistence_model_cls=BaseStatePersistenceModel,
    resource_type=MgmtResourceType.PROGRAM,
)


@WorkflowRegistry.register_workflow(prototype_state_machine_config)
class PrototypeStateMachine(BaseStateMachine):
    """A deliberately trivial workflow that proves the engine works end to end.

    It exists so the full loop (event on the queue -> manager -> state machine ->
    audit row) can be exercised before any real grantor domain lands in mgmt, and
    it covers the transition shapes the engine has to handle: the start event, a
    caller-driven transition, an automatic follow-on transition, and reaching a
    final state. Replace it with real workflows rather than growing it.
    """

    ### States
    states = States.from_enum(
        PrototypeState,
        initial=PrototypeState.START,
        final=[PrototypeState.END],
    )

    ### Events + transitions
    start_workflow = Event(
        states.START.to(states.IN_PROGRESS),
    )

    # `after` makes the engine send `finalize` on its own once this transition
    # completes. The audit listener attributes automatic transitions like that one
    # to the internal workflow user rather than whoever sent the event.
    complete = Event(
        states.IN_PROGRESS.to(states.FINALIZING, after="finalize"),
    )

    finalize = Event(
        states.FINALIZING.to(states.END),
    )

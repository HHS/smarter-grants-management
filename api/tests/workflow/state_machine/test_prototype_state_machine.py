from src.constants.lookup_constants import MgmtResourceType, MgmtWorkflowType
from src.workflow.state_machine.prototype_state_machine import (
    PrototypeState,
    PrototypeStateMachine,
    prototype_state_machine_config,
)
from src.workflow.state_persistence.program_persistence_model import ProgramPersistenceModel


def test_prototype_state_machine_config():
    assert prototype_state_machine_config.workflow_type == MgmtWorkflowType.PROTOTYPE_WORKFLOW
    assert prototype_state_machine_config.persistence_model_cls is ProgramPersistenceModel
    # Derived from the persistence model rather than configured separately
    assert prototype_state_machine_config.resource_type == MgmtResourceType.PROGRAM
    # Nothing about the prototype needs a single-active-workflow guarantee
    assert prototype_state_machine_config.allow_concurrent_workflow_for_resource is True
    assert prototype_state_machine_config.approval_mapping == {}


def test_prototype_state_machine_shape():
    assert PrototypeStateMachine.initial_state.value == PrototypeState.START
    assert PrototypeStateMachine.get_valid_events() == {
        "start_workflow",
        "complete",
        "finalize",
    }
    assert PrototypeStateMachine.get_valid_states() == [
        PrototypeState.START,
        PrototypeState.IN_PROGRESS,
        PrototypeState.FINALIZING,
        PrototypeState.END,
    ]


def test_prototype_state_machine_only_end_is_final():
    """Only END should deactivate a workflow - FINALIZING is passed straight through."""
    final_states = [state.value for state in PrototypeStateMachine.states if state.final]

    assert final_states == [PrototypeState.END]

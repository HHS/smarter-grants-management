import pytest

from src.constants.lookup_constants import ResourceType, WorkflowType
from src.workflow.state_machine.prototype_state_machine import PrototypeState, PrototypeStateMachine
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel
from src.workflow.state_persistence.program_persistence_model import ProgramPersistenceModel
from tests.db.models.factories import ProgramWorkflowFactory


def test_base_model_is_abstract():
    """Always use a derived class - the base can't be instantiated on its own."""
    with pytest.raises(TypeError, match="abstract"):
        BaseStatePersistenceModel(db_session=None, workflow=None)


def test_program_model_declares_its_resource_type():
    assert ProgramPersistenceModel.get_resource_type() == ResourceType.PROGRAM


def test_state_getter_reads_from_the_workflow(db_session, enable_factory_create):
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.IN_PROGRESS,
    )

    model = ProgramPersistenceModel(db_session=db_session, workflow=workflow)

    assert model.state == PrototypeState.IN_PROGRESS


def test_state_setter_writes_back_to_the_workflow(db_session, enable_factory_create):
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.START,
    )

    model = ProgramPersistenceModel(db_session=db_session, workflow=workflow)
    model.state = PrototypeState.IN_PROGRESS

    assert workflow.current_workflow_state == PrototypeState.IN_PROGRESS


def test_after_transition_tracks_whether_the_state_is_final(db_session, enable_factory_create):
    """is_active mirrors "not in a final state", which is what deactivates a workflow."""
    workflow = ProgramWorkflowFactory.create(
        workflow_type=WorkflowType.PROTOTYPE_WORKFLOW,
        current_workflow_state=PrototypeState.START,
        is_active=True,
    )
    model = ProgramPersistenceModel(db_session=db_session, workflow=workflow)

    states = {state.value: state for state in PrototypeStateMachine.states}

    model.after_transition(states[PrototypeState.IN_PROGRESS])
    assert workflow.is_active is True

    model.after_transition(states[PrototypeState.END])
    assert workflow.is_active is False

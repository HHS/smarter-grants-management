import abc

import grants_shared.adapters.db as db
import statemachine.state

from src.constants.lookup_constants import ResourceType
from src.db.models.workflow_models import Workflow


class BaseStatePersistenceModel(abc.ABC):
    """Base model for handling persistence of workflow state machine
    data to the database.

    Any class derived from this can change how logic works for
    setting up and validating a particular resource while getting
    the benefits of storing information back to the workflow table
    automatically for the state + is_active flags.

    Abstract on purpose - always define a derived class per resource type rather
    than using this directly. The resource type lives here (rather than alongside
    it on WorkflowConfig) so a workflow's persistence model and its resource type
    can't be configured out of sync with each other.
    """

    def __init__(self, db_session: db.Session, workflow: Workflow):
        self.db_session = db_session
        self.workflow = workflow

    @classmethod
    @abc.abstractmethod
    def get_resource_type(cls) -> ResourceType:
        """The type of resource that workflows using this model attach to."""

    @property
    def state(self) -> str:
        """Getter for the state"""
        return self.workflow.current_workflow_state

    @state.setter
    def state(self, value: str) -> None:
        """Setter for the state, anytime the state changes
        on the state machine, set that value in the workflow
        table.
        """
        self.workflow.current_workflow_state = value

    def after_transition(self, state: statemachine.state.State) -> None:
        """
        After processing a transition of states, always check
        if the workflow is still active based on whether it's
        in a final state.
        """
        self.workflow.is_active = not state.final

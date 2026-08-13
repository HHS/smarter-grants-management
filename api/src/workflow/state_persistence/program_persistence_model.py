from src.constants.lookup_constants import ResourceType
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel


class ProgramPersistenceModel(BaseStatePersistenceModel):
    """Persistence model for workflows that attach to a program.

    Nothing beyond the resource type yet - the base class already handles writing
    state and is_active back to workflow. Add program-specific loading or
    validation here when a real program workflow needs it.
    """

    @classmethod
    def get_resource_type(cls) -> ResourceType:
        return ResourceType.PROGRAM

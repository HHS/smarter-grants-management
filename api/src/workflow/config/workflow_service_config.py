import uuid

from pydantic import Field

from src.util.env_config import PydanticBaseEnvConfig


class WorkflowServiceConfig(PydanticBaseEnvConfig):
    """Configuration class for the workflow service as a whole."""

    # The user that automatic (engine-driven) state transitions are audited
    # against, so the audit history makes it clear which actions weren't taken by
    # the user who sent the event. The user must exist for those audits to commit.
    workflow_service_internal_user_id: uuid.UUID = Field(alias="WORKFLOW_SERVICE_INTERNAL_USER_ID")

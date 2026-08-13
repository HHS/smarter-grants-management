import uuid
from typing import Any

from pydantic import BaseModel

from src.constants.lookup_constants import MgmtWorkflowEventType, MgmtWorkflowType


class StartWorkflowEventContext(BaseModel):
    workflow_type: MgmtWorkflowType

    # The entity the workflow is for, referenced through its resource row rather
    # than a per-entity ID + type pair. Every authZ-relevant mgmt entity already
    # has a resource, so this works for any entity without a schema change - and
    # it's the same handle authZ checks against.
    mgmt_resource_id: uuid.UUID


class ProcessWorkflowEventContext(BaseModel):
    mgmt_workflow_id: uuid.UUID
    event_to_send: str


class WorkflowEvent(BaseModel):
    """An event representing what we send over SQS
    for starting/processing a workflow.
    """

    event_id: uuid.UUID
    acting_mgmt_user_id: uuid.UUID

    event_type: MgmtWorkflowEventType

    start_workflow_context: StartWorkflowEventContext | None = None
    process_workflow_context: ProcessWorkflowEventContext | None = None
    metadata: dict | None = None

    def get_log_extra(self) -> dict[str, Any]:
        log_extra = {
            "event_id": self.event_id,
            "acting_mgmt_user_id": self.acting_mgmt_user_id,
            "event_type": self.event_type,
        }
        if self.start_workflow_context is not None:
            log_extra |= {
                "workflow_type": self.start_workflow_context.workflow_type,
                "mgmt_resource_id": self.start_workflow_context.mgmt_resource_id,
            }
        if self.process_workflow_context is not None:
            log_extra |= {
                "mgmt_workflow_id": self.process_workflow_context.mgmt_workflow_id,
                "event_to_send": self.process_workflow_context.event_to_send,
            }

        return log_extra

import uuid
from datetime import datetime
from typing import Any

from grants_shared.adapters.db.type_decorators.postgres_type_decorators import LookupColumn
from grants_shared.db.models.base import TimestampMixin
from sqlalchemy import UUID, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.constants.lookup_constants import (
    MgmtApprovalResponseType,
    MgmtApprovalType,
    MgmtWorkflowType,
)
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import (
    LkMgmtApprovalResponseType,
    LkMgmtApprovalType,
    LkMgmtWorkflowType,
)
from src.db.models.resource_models import MgmtResource
from src.db.models.user_models import MgmtUser


class MgmtWorkflow(GrantorSchemaTable, TimestampMixin):
    """
    Workflow model for tracking the state of a given instance of a workflow.

    The entity a workflow is attached to is always referenced through the resource
    table - every authZ-relevant entity already has a resource row (created by the
    resource automation flush hook), so there are no per-entity FK columns here.

    Attributes:
        mgmt_workflow_id: Primary key, UUID
        mgmt_workflow_type_id: Foreign key to lk_mgmt_workflow_type table
        mgmt_resource_id: Foreign key to the mgmt_resource table for the entity the workflow is for
        current_workflow_state: Text field describing the current state of the workflow
        is_active: Boolean flag indicating if the workflow is active, set to False when the workflow hits an end state
    """

    __tablename__ = "mgmt_workflow"

    mgmt_workflow_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    workflow_type: Mapped[MgmtWorkflowType] = mapped_column(
        "mgmt_workflow_type_id",
        LookupColumn(LkMgmtWorkflowType),
        ForeignKey(LkMgmtWorkflowType.mgmt_workflow_type_id),
    )

    mgmt_resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(MgmtResource.mgmt_resource_id), index=True
    )
    resource: Mapped[MgmtResource] = relationship(MgmtResource)

    current_workflow_state: Mapped[str]

    is_active: Mapped[bool]

    workflow_event_history: Mapped[list[MgmtWorkflowEventHistory]] = relationship(
        back_populates="workflow", uselist=True, cascade="all, delete-orphan"
    )

    workflow_audits: Mapped[list[MgmtWorkflowAudit]] = relationship(
        back_populates="workflow", uselist=True, cascade="all, delete-orphan"
    )

    workflow_approvals: Mapped[list[MgmtWorkflowApproval]] = relationship(
        back_populates="workflow", uselist=True, cascade="all, delete-orphan"
    )

    def get_log_extra(self) -> dict[str, Any]:
        return {
            "mgmt_workflow_id": self.mgmt_workflow_id,
            "workflow_type": self.workflow_type,
            "current_workflow_state": self.current_workflow_state,
            "is_active": self.is_active,
            "mgmt_resource_id": self.mgmt_resource_id,
        }


class MgmtWorkflowEventHistory(GrantorSchemaTable, TimestampMixin):
    """
    MgmtWorkflowEventHistory model to store the SQS events in the DB.

    Attributes:
        mgmt_workflow_event_history_id: Primary key, UUID
        mgmt_workflow_id: Foreign key to mgmt_workflow table, note the field is nullable in this table
        event_data: JSONB field containing event data
        sent_at: Timestamp indicating when the event was sent
        is_successfully_processed: Boolean flag indicating if the event was processed successfully
    """

    __tablename__ = "mgmt_workflow_event_history"

    mgmt_workflow_event_history_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    mgmt_workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID, ForeignKey(MgmtWorkflow.mgmt_workflow_id)
    )
    workflow: Mapped[MgmtWorkflow | None] = relationship(
        MgmtWorkflow, back_populates="workflow_event_history"
    )

    event_data: Mapped[dict] = mapped_column(JSONB)

    sent_at: Mapped[datetime]

    is_successfully_processed: Mapped[bool]


class MgmtWorkflowAudit(GrantorSchemaTable, TimestampMixin):
    """
    MgmtWorkflowAudit model for tracking all state transitions on a workflow.

    Attributes:
        mgmt_workflow_audit_id: Primary key, UUID
        mgmt_workflow_id: Foreign key to mgmt_workflow table
        acting_mgmt_user_id: Foreign key to mgmt_user table indicating who performed the action
        transition_event: Text field describing the transition event
        source_state: Text field indicating the source state before the transition
        target_state: Text field indicating the target state after the transition
        mgmt_workflow_event_history_id: Foreign key to mgmt_workflow_event_history table
        audit_metadata: JSONB field for additional metadata about the audit
    """

    __tablename__ = "mgmt_workflow_audit"

    mgmt_workflow_audit_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    mgmt_workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(MgmtWorkflow.mgmt_workflow_id), nullable=False
    )
    workflow: Mapped[MgmtWorkflow] = relationship(MgmtWorkflow, back_populates="workflow_audits")

    acting_mgmt_user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(MgmtUser.mgmt_user_id))
    acting_user: Mapped[MgmtUser] = relationship(MgmtUser)

    transition_event: Mapped[str]

    source_state: Mapped[str]

    target_state: Mapped[str]

    mgmt_workflow_event_history_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(MgmtWorkflowEventHistory.mgmt_workflow_event_history_id)
    )
    event: Mapped[MgmtWorkflowEventHistory] = relationship(MgmtWorkflowEventHistory)

    audit_metadata: Mapped[dict | None] = mapped_column(JSONB)


class MgmtWorkflowApproval(GrantorSchemaTable, TimestampMixin):
    """
    MgmtWorkflowApproval model to store the approval information.

    Attributes:
        mgmt_workflow_approval_id: Primary key, UUID
        mgmt_workflow_id: Foreign key to mgmt_workflow table
        approving_mgmt_user_id: Foreign key to mgmt_user table indicating who approved the workflow
        mgmt_approval_type_id: Foreign key to lk_mgmt_approval_type table indicating the type of approval
        mgmt_workflow_event_history_id: Foreign key to mgmt_workflow_event_history table indicating the event that triggered the approval
        is_still_valid: Boolean flag indicating if the approval is still valid
        mgmt_approval_response_type_id: Foreign key to lk_mgmt_approval_response_type table indicating the response type
    """

    __tablename__ = "mgmt_workflow_approval"

    mgmt_workflow_approval_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    mgmt_workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(MgmtWorkflow.mgmt_workflow_id), nullable=False
    )
    workflow: Mapped[MgmtWorkflow] = relationship(MgmtWorkflow, back_populates="workflow_approvals")

    approving_mgmt_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(MgmtUser.mgmt_user_id)
    )
    approving_user: Mapped[MgmtUser] = relationship(MgmtUser)

    approval_type: Mapped[MgmtApprovalType] = mapped_column(
        "mgmt_approval_type_id",
        LookupColumn(LkMgmtApprovalType),
        ForeignKey(LkMgmtApprovalType.mgmt_approval_type_id),
        index=True,
    )

    mgmt_workflow_event_history_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(MgmtWorkflowEventHistory.mgmt_workflow_event_history_id)
    )
    event: Mapped[MgmtWorkflowEventHistory] = relationship(MgmtWorkflowEventHistory)

    is_still_valid: Mapped[bool]

    comment: Mapped[str | None]

    approval_response_type: Mapped[MgmtApprovalResponseType] = mapped_column(
        "mgmt_approval_response_type_id",
        LookupColumn(LkMgmtApprovalResponseType),
        ForeignKey(LkMgmtApprovalResponseType.mgmt_approval_response_type_id),
        index=True,
    )

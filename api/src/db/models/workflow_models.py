import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.adapters.db.lookup.lookup_column import LookupColumn
from src.constants.lookup_constants import ApprovalResponseType, ApprovalType, WorkflowType
from src.db.models.base import TimestampMixin
from src.db.models.grantor_schema_table import GrantorSchemaTable
from src.db.models.lookup_models import LkApprovalResponseType, LkApprovalType, LkWorkflowType
from src.db.models.resource_models import Resource
from src.db.models.user_models import User


class Workflow(GrantorSchemaTable, TimestampMixin):
    """
    Workflow model for tracking the state of a given instance of a workflow.

    The entity a workflow is attached to is always referenced through the resource
    table - every authZ-relevant entity already has a resource row (created by the
    resource automation flush hook), so there are no per-entity FK columns here.

    Attributes:
        workflow_id: Primary key, UUID
        workflow_type_id: Foreign key to lk_workflow_type table
        resource_id: Foreign key to the resource table for the entity the workflow is for
        current_workflow_state: Text field describing the current state of the workflow
        is_active: Boolean flag indicating if the workflow is active, set to False when the workflow hits an end state
    """

    __tablename__ = "workflow"

    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    workflow_type: Mapped[WorkflowType] = mapped_column(
        "workflow_type_id",
        LookupColumn(LkWorkflowType),
        ForeignKey(LkWorkflowType.workflow_type_id),
    )

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Resource.resource_id), index=True
    )
    resource: Mapped[Resource] = relationship(Resource)

    current_workflow_state: Mapped[str]

    is_active: Mapped[bool]

    workflow_event_history: Mapped[list[WorkflowEventHistory]] = relationship(
        back_populates="workflow", uselist=True, cascade="all, delete-orphan"
    )

    workflow_audits: Mapped[list[WorkflowAudit]] = relationship(
        back_populates="workflow", uselist=True, cascade="all, delete-orphan"
    )

    workflow_approvals: Mapped[list[WorkflowApproval]] = relationship(
        back_populates="workflow", uselist=True, cascade="all, delete-orphan"
    )

    def get_log_extra(self, include_joined_values: bool = False) -> dict[str, Any]:
        log_extra = {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "current_workflow_state": self.current_workflow_state,
            "is_active": self.is_active,
            "resource_id": self.resource_id,
        }

        if include_joined_values:
            log_extra |= {"resource_type": self.resource.resource_type}

        return log_extra


class WorkflowEventHistory(GrantorSchemaTable, TimestampMixin):
    """
    WorkflowEventHistory model to store the SQS events in the DB.

    Attributes:
        workflow_event_history_id: Primary key, UUID - the event_id the caller
            generated and put on the queue, not an ID we mint here. Keying on it is what
            lets the ID handed back by the event API find this row later.
        workflow_id: Foreign key to workflow table, note the field is nullable in this table
        event_data: JSONB field containing event data
        sent_at: Timestamp indicating when the event was sent
        is_successfully_processed: Boolean flag indicating if the event was processed successfully
    """

    __tablename__ = "workflow_event_history"

    workflow_event_history_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    workflow_id: Mapped[uuid.UUID | None] = mapped_column(UUID, ForeignKey(Workflow.workflow_id))
    workflow: Mapped[Workflow | None] = relationship(
        Workflow, back_populates="workflow_event_history"
    )

    event_data: Mapped[dict] = mapped_column(JSONB)

    sent_at: Mapped[datetime]

    is_successfully_processed: Mapped[bool]


class WorkflowAudit(GrantorSchemaTable, TimestampMixin):
    """
    WorkflowAudit model for tracking all state transitions on a workflow.

    Attributes:
        workflow_audit_id: Primary key, UUID
        workflow_id: Foreign key to workflow table
        acting_user_id: Foreign key to user table indicating who performed the action
        transition_event: Text field describing the transition event
        source_state: Text field indicating the source state before the transition
        target_state: Text field indicating the target state after the transition
        workflow_event_history_id: Foreign key to workflow_event_history table
        audit_metadata: JSONB field for additional metadata about the audit
    """

    __tablename__ = "workflow_audit"

    workflow_audit_id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Workflow.workflow_id), nullable=False
    )
    workflow: Mapped[Workflow] = relationship(Workflow, back_populates="workflow_audits")

    acting_user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(User.user_id))
    acting_user: Mapped[User] = relationship(User)

    transition_event: Mapped[str]

    source_state: Mapped[str]

    target_state: Mapped[str]

    workflow_event_history_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(WorkflowEventHistory.workflow_event_history_id)
    )
    event: Mapped[WorkflowEventHistory] = relationship(WorkflowEventHistory)

    audit_metadata: Mapped[dict | None] = mapped_column(JSONB)


class WorkflowApproval(GrantorSchemaTable, TimestampMixin):
    """
    WorkflowApproval model to store the approval information.

    Attributes:
        workflow_approval_id: Primary key, UUID
        workflow_id: Foreign key to workflow table
        approving_user_id: Foreign key to user table indicating who approved the workflow
        approval_type_id: Foreign key to lk_approval_type table indicating the type of approval
        workflow_event_history_id: Foreign key to workflow_event_history table indicating the event that triggered the approval
        is_still_valid: Boolean flag indicating if the approval is still valid
        approval_response_type_id: Foreign key to lk_approval_response_type table indicating the response type
    """

    __tablename__ = "workflow_approval"

    workflow_approval_id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True, default=uuid.uuid4
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(Workflow.workflow_id), nullable=False
    )
    workflow: Mapped[Workflow] = relationship(Workflow, back_populates="workflow_approvals")

    approving_user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey(User.user_id))
    approving_user: Mapped[User] = relationship(User)

    approval_type: Mapped[ApprovalType] = mapped_column(
        "approval_type_id",
        LookupColumn(LkApprovalType),
        ForeignKey(LkApprovalType.approval_type_id),
        index=True,
    )

    workflow_event_history_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey(WorkflowEventHistory.workflow_event_history_id)
    )
    event: Mapped[WorkflowEventHistory] = relationship(WorkflowEventHistory)

    is_still_valid: Mapped[bool]

    comment: Mapped[str | None]

    approval_response_type: Mapped[ApprovalResponseType] = mapped_column(
        "approval_response_type_id",
        LookupColumn(LkApprovalResponseType),
        ForeignKey(LkApprovalResponseType.approval_response_type_id),
        index=True,
    )

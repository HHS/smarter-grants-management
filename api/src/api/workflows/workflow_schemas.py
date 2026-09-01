from typing import Any

from marshmallow import ValidationError, validates_schema

from src.api.schemas.extension import (
    MarshmallowErrorContainer,
    Schema,
    SchemaValidationError,
    fields,
    validators,
)
from src.api.schemas.response_schema import AbstractResponseSchema, PaginationMixinSchema
from src.pagination.pagination_schema import generate_pagination_schema
from marshmallow import ValidationError, validates_schema

from src.constants.lookup_constants import (
    ApprovalResponseType,
    ApprovalType,
    Privilege,
    ResourceType,
    WorkflowEventType,
    WorkflowType,
)


class StartWorkflowContextSchema(Schema):
    workflow_type = fields.Enum(
        WorkflowType,
        required=True,
        metadata={"description": "The type of workflow to initiate"},
    )
    resource_id = fields.UUID(
        required=True,
        metadata={
            "description": "The resource ID of the entity to associate with the workflow - different workflows require different resource types."
        },
    )


class ProcessWorkflowContextSchema(Schema):
    workflow_id = fields.UUID(
        required=True, metadata={"description": "The ID of the existing workflow to progress"}
    )
    event_to_send = fields.String(
        required=True,
        validate=validators.Length(min=1),
        metadata={
            "description": "The specific event/action to trigger in the state machine",
            "example": "complete",
        },
    )


class WorkflowEventRequestSchema(Schema):
    event_type = fields.Enum(
        WorkflowEventType,
        required=True,
        metadata={
            "description": "The category of event: either starting a new workflow or processing an existing one"
        },
    )
    start_workflow_context = fields.Nested(
        StartWorkflowContextSchema,
        required=False,
        metadata={
            "description": "Context and entities required to initialize a new workflow. Only allowed if event_type is 'start_workflow'."
        },
    )
    process_workflow_context = fields.Nested(
        ProcessWorkflowContextSchema,
        required=False,
        metadata={
            "description": "Information required to progress an existing workflow state. Only allowed if event_type is 'process_workflow'."
        },
    )
    metadata = fields.Dict(
        required=False,
        load_default={},
        metadata={
            "description": "A freeform JSON object for the particular event, if needed.",
            "example": {"source_system": "grants_solutions", "priority": "high"},
        },
    )

    @validates_schema
    def validate_context(self, data: dict[str, Any], **kwargs: Any) -> None:
        event_type = data.get("event_type")
        start_ctx = data.get("start_workflow_context")
        process_ctx = data.get("process_workflow_context")

        if event_type == WorkflowEventType.START_WORKFLOW:
            if not start_ctx:
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.REQUIRED, "start_workflow_context is required"
                        )
                    ],
                    "start_workflow_context",
                )

            if process_ctx:
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.INVALID,
                            "process_workflow_context should not be provided",
                        )
                    ],
                    "process_workflow_context",
                )

        if event_type == WorkflowEventType.PROCESS_WORKFLOW:
            if not process_ctx:
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.REQUIRED, "process_workflow_context is required"
                        )
                    ],
                    "process_workflow_context",
                )
            if start_ctx:
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.INVALID,
                            "start_workflow_context should not be provided",
                        )
                    ],
                    "start_workflow_context",
                )


class WorkflowEventResponseDataSchema(Schema):
    event_id = fields.UUID(metadata={"description": "The tracking ID for the workflow event"})


class WorkflowEventResponseSchema(AbstractResponseSchema):
    data = fields.Nested(WorkflowEventResponseDataSchema)


####################################
# Workflow read schemas
####################################


class WorkflowUserSchema(Schema):
    user_id = fields.UUID(metadata={"description": "The user's unique identifier"})
    email = fields.String(
        allow_none=True,
        metadata={
            "description": "The user's email address, null if they have no login",
            "example": "user@example.com",
        },
    )


class WorkflowEventRefSchema(Schema):
    event_id = fields.UUID(
        metadata={"description": "The ID of the event that produced this record"}
    )
    sent_at = fields.DateTime(metadata={"description": "When the event was sent"})


class WorkflowAuditEventSchema(Schema):
    workflow_audit_id = fields.UUID(
        metadata={"description": "The audit record's unique identifier"}
    )
    acting_user = fields.Nested(
        WorkflowUserSchema, metadata={"description": "The user who performed the transition"}
    )
    transition_event = fields.String(
        metadata={"description": "The event that triggered the transition"}
    )
    source_state = fields.String(metadata={"description": "The state before the transition"})
    target_state = fields.String(metadata={"description": "The state after the transition"})
    event = fields.Nested(
        WorkflowEventRefSchema,
        metadata={"description": "The event that triggered this transition"},
    )
    audit_metadata = fields.Dict(
        allow_none=True,
        metadata={"description": "Additional metadata recorded with the transition"},
    )
    created_at = fields.DateTime(dump_only=True)


class WorkflowApprovalSchema(Schema):
    workflow_approval_id = fields.UUID(
        metadata={"description": "The approval record's unique identifier"}
    )
    approving_user = fields.Nested(
        WorkflowUserSchema, metadata={"description": "The user who gave this approval"}
    )
    event_id = fields.UUID(
        metadata={"description": "The ID of the event that recorded this approval"}
    )
    is_still_valid = fields.Boolean(
        metadata={"description": "Whether this approval is still in effect"}
    )
    comment = fields.String(
        allow_none=True, metadata={"description": "An optional comment left with the approval"}
    )
    approval_type = fields.Enum(ApprovalType, metadata={"description": "The type of approval"})
    approval_response_type = fields.Enum(
        ApprovalResponseType, metadata={"description": "The response given for this approval"}
    )
    created_at = fields.DateTime(dump_only=True)


class WorkflowApprovalConfigEntrySchema(Schema):
    approval_type = fields.Enum(
        ApprovalType, metadata={"description": "The type of approval this event represents"}
    )
    required_privileges = fields.List(
        fields.Enum(Privilege),
        metadata={"description": "The privileges required to give this approval"},
    )
    allowed_approval_response_types = fields.List(
        fields.Enum(ApprovalResponseType),
        metadata={"description": "The response types this approval accepts"},
    )
    possible_users = fields.List(
        fields.Nested(WorkflowUserSchema),
        metadata={"description": "The users eligible to give this approval"},
    )


class WorkflowGetResponseDataSchema(Schema):
    workflow_id = fields.UUID(metadata={"description": "The workflow's unique identifier"})
    workflow_type = fields.Enum(WorkflowType, metadata={"description": "The type of workflow"})
    current_workflow_state = fields.String(metadata={"description": "The workflow's current state"})
    is_active = fields.Boolean(metadata={"description": "Whether the workflow is still active"})
    resource_id = fields.UUID(metadata={"description": "The resource the workflow is attached to"})
    resource_type = fields.Enum(
        ResourceType,
        metadata={"description": "The type of resource the workflow is attached to"},
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    workflow_audit_events = fields.List(
        fields.Nested(WorkflowAuditEventSchema),
        metadata={"description": "The workflow's audit history, sorted oldest to newest"},
    )
    workflow_approvals = fields.List(
        fields.Nested(WorkflowApprovalSchema),
        metadata={
            "description": "The approvals recorded against the workflow, sorted oldest to newest"
        },
    )
    workflow_approval_config = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(WorkflowApprovalConfigEntrySchema),
        metadata={
            "description": "For each event that requires an approval, who can give it and how"
        },
    )
    valid_events = fields.List(
        fields.String(),
        metadata={
            "description": "The events that can legally be sent next, given the current state"
        },
    )


class WorkflowGetResponseSchema(AbstractResponseSchema):
    data = fields.Nested(WorkflowGetResponseDataSchema)


class WorkflowAuditRequestSchema(Schema):
    pagination = fields.Nested(
        generate_pagination_schema(
            cls_name="WorkflowAuditPaginationSchema",
            order_by_fields=["created_at"],
            default_sort_order=[{"order_by": "created_at", "sort_direction": "descending"}],
            default_page_size=25,
            default_page_offset=1,
        ),
        required=True,
    )


class WorkflowAuditResponseSchema(AbstractResponseSchema, PaginationMixinSchema):
    data = fields.List(fields.Nested(WorkflowAuditEventSchema))

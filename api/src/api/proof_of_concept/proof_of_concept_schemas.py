from enum import StrEnum

from src.api.schemas.extension import Schema, fields


class OpportunityStatus(StrEnum):
    FORECASTED = "forecasted"
    POSTED = "posted"
    CLOSED = "closed"
    ARCHIVED = "archived"


class OpportunitySummarySchema(Schema):
    post_date = fields.Date(
        allow_none=True, metadata={"description": "The date the opportunity was posted"}
    )


class OpportunityDataSchema(Schema):
    opportunity_id = fields.UUID(
        required=True, metadata={"description": "The unique identifier for the opportunity"}
    )
    opportunity_title = fields.String(
        allow_none=True, metadata={"description": "The title of the opportunity"}
    )
    opportunity_status = fields.Enum(
        OpportunityStatus,
        allow_none=True,
        metadata={"description": "The current status of the opportunity"},
    )
    summary = fields.Nested(
        OpportunitySummarySchema(),
        allow_none=True,
        metadata={"description": "Summary information about the opportunity"},
    )


class OpportunityGetResponseSchema(Schema):
    data = fields.Nested(
        OpportunityDataSchema(),
        metadata={"description": "The opportunity data"},
    )

from enum import StrEnum

from grants_shared.api.schemas.extension import Schema, fields


class OpportunityStatus(StrEnum):
    FORECASTED = "forecasted"
    POSTED = "posted"
    CLOSED = "closed"
    ARCHIVED = "archived"


class OpportunitySummarySchema(Schema):
    post_date = fields.Date(allow_none=True)


class OpportunityDataSchema(Schema):
    opportunity_id = fields.UUID(required=True)
    opportunity_title = fields.String(allow_none=True)
    opportunity_status = fields.Enum(OpportunityStatus, by_value=True, allow_none=True)
    summary = fields.Nested(OpportunitySummarySchema(), allow_none=True)


class OpportunityGetResponseSchema(Schema):
    data = fields.Nested(OpportunityDataSchema(), required=True)

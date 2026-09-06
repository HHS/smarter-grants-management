from marshmallow import ValidationError, validates_schema

from src.api.schemas.extension import (
    MarshmallowErrorContainer,
    Schema,
    SchemaValidationError,
    fields,
    validators,
)
from src.api.schemas.response_schema import AbstractResponseSchema, PaginationMixinSchema
from src.constants.lookup_constants import (
    ApplicantType,
    CompetitionOpenToApplicant,
    FundingCategory,
    FundingInstrument,
    OpportunityCategory,
)
from src.pagination.pagination_schema import generate_pagination_schema


class AssistanceListingSchema(Schema):
    assistance_listing_id = fields.UUID()
    assistance_listing_number = fields.String()
    program_title = fields.String()


class OpportunityAssistanceListingSchema(Schema):
    opportunity_assistance_listing_id = fields.UUID()
    assistance_listing = fields.Nested(AssistanceListingSchema)


class FileAttachmentSchema(Schema):
    file_attachment_id = fields.UUID()
    file_location = fields.String()
    file_name = fields.String()
    mime_type = fields.String()
    file_description = fields.String(allow_none=True)
    file_size_bytes = fields.Integer()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class OpportunityAttachmentSchema(Schema):
    opportunity_attachment_id = fields.UUID()
    file_attachment = fields.Nested(FileAttachmentSchema)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class OpportunitySummarySchema(Schema):
    opportunity_summary_id = fields.UUID()
    summary_description = fields.String()
    is_cost_sharing = fields.Boolean()
    is_forecast = fields.Boolean()

    post_timestamp = fields.DateTime()
    close_timestamp = fields.DateTime(allow_none=True)
    close_timestamp_description = fields.String(allow_none=True)
    archive_timestamp = fields.DateTime(allow_none=True)

    expected_number_of_awards = fields.Integer(allow_none=True)
    estimated_total_program_funding = fields.Integer(allow_none=True)
    award_floor = fields.Integer(allow_none=True)
    award_ceiling = fields.Integer(allow_none=True)

    additional_info_url = fields.String(allow_none=True)
    additional_info_url_description = fields.String(allow_none=True)

    forecasted_post_timestamp = fields.DateTime(allow_none=True)
    forecasted_close_timestamp = fields.DateTime(allow_none=True)
    forecasted_close_timestamp_description = fields.String(allow_none=True)
    forecasted_award_timestamp = fields.DateTime(allow_none=True)
    forecasted_project_start_timestamp = fields.DateTime(allow_none=True)
    fiscal_year = fields.Integer(allow_none=True)

    funding_instruments = fields.List(fields.Enum(FundingInstrument))
    funding_categories = fields.List(fields.Enum(FundingCategory))
    applicant_types = fields.List(fields.Enum(ApplicantType))

    funding_category_description = fields.String(allow_none=True)
    applicant_eligibility_description = fields.String(allow_none=True)

    agency_contact_description = fields.String(allow_none=True)
    agency_email_address = fields.String(allow_none=True)
    agency_email_address_description = fields.String(allow_none=True)

    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class CompetitionFormSchema(Schema):
    competition_form_id = fields.UUID()
    form_id = fields.UUID()
    is_required = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class CompetitionInstructionSchema(Schema):
    competition_instruction_id = fields.UUID()
    file_attachment = fields.Nested(FileAttachmentSchema)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class CompetitionSchema(Schema):
    competition_id = fields.UUID()
    public_competition_id = fields.String(allow_none=True)
    competition_title = fields.String(allow_none=True)
    opening_timestamp = fields.DateTime(allow_none=True)
    closing_timestamp = fields.DateTime(allow_none=True)
    grace_period = fields.Integer(allow_none=True)
    contact_info = fields.String(allow_none=True)
    opportunity_assistance_listing_id = fields.UUID(allow_none=True)

    open_to_applicants = fields.List(fields.Enum(CompetitionOpenToApplicant))
    competition_forms = fields.List(fields.Nested(CompetitionFormSchema))
    competition_instructions = fields.List(fields.Nested(CompetitionInstructionSchema))

    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class OpportunitySchema(Schema):
    opportunity_id = fields.UUID()
    opportunity_group_id = fields.UUID()
    opportunity_number = fields.String()
    opportunity_title = fields.String()
    tagline = fields.String()
    purpose_statement = fields.String()
    category = fields.Enum(OpportunityCategory, allow_none=True)
    category_explanation = fields.String(allow_none=True)

    opportunity_assistance_listings = fields.List(fields.Nested(OpportunityAssistanceListingSchema))
    forecast_summary = fields.Nested(OpportunitySummarySchema, allow_none=True)
    non_forecast_summary = fields.Nested(OpportunitySummarySchema, allow_none=True)
    attachments = fields.List(
        fields.Nested(OpportunityAttachmentSchema),
        attribute="opportunity_attachments",
    )
    competitions = fields.List(fields.Nested(CompetitionSchema))

    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class OpportunityCreateRequestSchema(Schema):
    opportunity_group_id = fields.UUID(required=True)
    opportunity_number = fields.String(
        required=True,
        validate=validators.Length(max=40),
    )
    opportunity_title = fields.String(
        required=True,
        validate=validators.Length(max=255),
    )
    tagline = fields.String(
        required=True,
        validate=validators.Length(max=255),
    )
    purpose_statement = fields.String(
        required=True,
        validate=validators.Length(max=255),
    )
    category = fields.Enum(OpportunityCategory, required=True)
    category_explanation = fields.String(
        allow_none=True,
        validate=validators.Length(max=255),
    )
    assistance_listing_number = fields.String(
        required=True,
        validate=validators.Length(max=6),
    )

    @validates_schema
    def validate_category_explanation(self, data: dict, **kwargs: dict) -> None:
        if data.get("category") == OpportunityCategory.OTHER:
            explanation = data.get("category_explanation") or ""
            if explanation.strip() == "":
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.REQUIRED,
                            "Explanation of the category is required when category is 'other'.",
                        )
                    ],
                    "category_explanation",
                )


class OpportunityUpdateRequestSchema(Schema):
    opportunity_title = fields.String(
        required=True,
        validate=validators.Length(max=255),
    )
    tagline = fields.String(
        required=True,
        validate=validators.Length(max=255),
    )
    purpose_statement = fields.String(
        required=True,
        validate=validators.Length(max=255),
    )
    category = fields.Enum(OpportunityCategory, required=True)
    category_explanation = fields.String(
        allow_none=True,
        load_default=None,
        validate=validators.Length(max=255),
    )

    @validates_schema
    def validate_category_explanation(self, data: dict, **kwargs: dict) -> None:
        if data.get("category") == OpportunityCategory.OTHER:
            explanation = data.get("category_explanation") or ""
            if explanation.strip() == "":
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.REQUIRED,
                            "Explanation of the category is required when category is 'other'.",
                        )
                    ],
                    "category_explanation",
                )


class OpportunityListFilterSchema(Schema):
    opportunity_group_id = fields.UUID(allow_none=True)
    query = fields.String(
        allow_none=True,
        metadata={"description": "Case-insensitive search across opportunity number and title"},
    )


class OpportunityListRequestSchema(Schema):
    filters = fields.Nested(OpportunityListFilterSchema())

    pagination = fields.Nested(
        generate_pagination_schema(
            "OpportunityListPaginationSchema",
            [
                "opportunity_id",
                "opportunity_number",
                "opportunity_title",
                "created_at",
            ],
            default_sort_order=[{"order_by": "created_at", "sort_direction": "descending"}],
            default_page_size=25,
            default_page_offset=1,
        ),
        required=True,
    )


class OpportunityResponseSchema(AbstractResponseSchema):
    data = fields.Nested(OpportunitySchema)


class OpportunityListResponseSchema(AbstractResponseSchema, PaginationMixinSchema):
    data = fields.List(fields.Nested(OpportunitySchema))

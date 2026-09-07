from datetime import timedelta

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
    OpportunityAuditEvent,
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


class OpportunityAttachmentCreateRequestSchema(Schema):
    pending_file_id = fields.UUID(required=True)


class OpportunityAttachmentResponseSchema(AbstractResponseSchema):
    data = fields.Nested(OpportunityAttachmentSchema)


class OpportunityAttachmentDeleteResponseSchema(AbstractResponseSchema):
    pass


class CompetitionRequestBaseSchema(Schema):
    competition_title = fields.String(required=True, validate=validators.Length(max=255))
    public_competition_id = fields.String(allow_none=True, validate=validators.Length(max=255))
    opening_timestamp = fields.DateTime(required=True)
    closing_timestamp = fields.DateTime(required=True)
    grace_period = fields.Integer(allow_none=True, validate=validators.Range(min=0))
    contact_info = fields.String(required=True, validate=validators.Length(max=4000))
    open_to_applicants = fields.List(
        fields.Enum(CompetitionOpenToApplicant), required=True, validate=validators.Length(min=1)
    )

    @validates_schema
    def validate_timestamps(self, data: dict, **kwargs: dict) -> None:
        if data["opening_timestamp"] > data["closing_timestamp"]:
            raise ValidationError(
                [
                    MarshmallowErrorContainer(
                        SchemaValidationError.INVALID,
                        "Opening timestamp must be less than or equal to closing timestamp",
                    )
                ]
            )


class CompetitionCreateRequestSchema(CompetitionRequestBaseSchema):
    pass


class CompetitionUpdateRequestSchema(CompetitionRequestBaseSchema):
    pass


class CompetitionResponseSchema(AbstractResponseSchema):
    data = fields.Nested("CompetitionSchema")


class CompetitionInstructionCreateRequestSchema(Schema):
    pending_file_id = fields.UUID(required=True)


class CompetitionInstructionResponseSchema(AbstractResponseSchema):
    data = fields.Nested("CompetitionInstructionSchema")


class CompetitionInstructionDeleteResponseSchema(AbstractResponseSchema):
    pass


class OpportunityAuditFilterSchema(Schema):
    opportunity_audit_event = fields.List(fields.Enum(OpportunityAuditEvent), allow_none=True)


class OpportunityAuditRequestSchema(Schema):
    filters = fields.Nested(OpportunityAuditFilterSchema(), allow_none=True)
    pagination = fields.Nested(
        generate_pagination_schema(
            "OpportunityAuditPaginationSchema",
            [
                "created_at",
                "opportunity_group_audit_id",
            ],
            default_sort_order=[{"order_by": "created_at", "sort_direction": "descending"}],
            default_page_size=25,
            default_page_offset=1,
        ),
        required=True,
    )


class OpportunityAuditSchema(Schema):
    opportunity_group_audit_id = fields.UUID()
    opportunity_group_id = fields.UUID()
    opportunity_audit_event = fields.Enum(OpportunityAuditEvent)
    user_id = fields.UUID()
    opportunity_id = fields.UUID(allow_none=True)
    opportunity_summary_id = fields.UUID(allow_none=True)
    competition_id = fields.UUID(allow_none=True)
    audit_metadata = fields.Dict(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class OpportunityAuditResponseSchema(AbstractResponseSchema, PaginationMixinSchema):
    data = fields.List(fields.Nested(OpportunityAuditSchema))


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


class OpportunitySummaryBaseRequestSchema(Schema):
    summary_description = fields.String(
        required=True,
        validate=validators.WordLimit(max=500),
    )
    is_cost_sharing = fields.Boolean(required=True)

    post_timestamp = fields.DateTime(required=True)
    close_timestamp = fields.DateTime(allow_none=True)
    close_timestamp_description = fields.String(allow_none=True)
    archive_timestamp = fields.DateTime(allow_none=True)

    expected_number_of_awards = fields.Integer(
        allow_none=True,
        validate=validators.Range(min=0, max=999_999_999_999_999),
    )
    estimated_total_program_funding = fields.Integer(
        allow_none=True,
        validate=validators.Range(min=0, max=999_999_999_999_999),
    )
    award_floor = fields.Integer(
        required=True,
        allow_none=True,
        validate=validators.Range(min=0, max=999_999_999_999_999),
    )
    award_ceiling = fields.Integer(
        required=True,
        allow_none=True,
        validate=validators.Range(min=0, max=999_999_999_999_999),
    )

    additional_info_url = fields.String(
        allow_none=True,
        validate=validators.Length(max=250),
    )
    additional_info_url_description = fields.String(
        allow_none=True,
        validate=validators.Length(max=250),
    )

    forecasted_post_timestamp = fields.DateTime(allow_none=True)
    forecasted_close_timestamp = fields.DateTime(allow_none=True)
    forecasted_close_timestamp_description = fields.String(
        allow_none=True,
        validate=validators.Length(max=255),
    )
    forecasted_award_timestamp = fields.DateTime(allow_none=True)
    forecasted_project_start_timestamp = fields.DateTime(allow_none=True)
    fiscal_year = fields.Integer(
        allow_none=True,
        validate=validators.Range(min=1900, max=2100),
    )

    funding_categories = fields.List(
        fields.Enum(FundingCategory),
        required=True,
        validate=validators.Length(min=1),
    )
    funding_category_description = fields.String(
        allow_none=True,
        validate=validators.Length(max=2500),
    )
    funding_instruments = fields.List(
        fields.Enum(FundingInstrument),
        required=True,
        validate=validators.Length(min=1),
    )
    applicant_types = fields.List(
        fields.Enum(ApplicantType),
        required=True,
        validate=validators.Length(min=1),
    )
    applicant_eligibility_description = fields.String(
        allow_none=True,
        validate=validators.Length(max=4000),
    )

    agency_contact_description = fields.String(
        required=True,
        allow_none=True,
        validate=validators.Length(max=1000),
    )
    agency_email_address = fields.String(
        required=True,
        allow_none=True,
        validate=validators.Length(max=130),
    )
    agency_email_address_description = fields.String(
        required=True,
        allow_none=True,
        validate=validators.Length(max=108),
    )

    @validates_schema
    def validate_award_values(self, data: dict, **kwargs: dict) -> None:
        if data.get("award_floor") is not None and data.get("award_ceiling") is not None:
            if data["award_floor"] > data["award_ceiling"]:
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.INVALID,
                            "Award floor must be less than or equal to award ceiling",
                        )
                    ]
                )

    @validates_schema
    def validate_timestamps(self, data: dict, **kwargs: dict) -> None:
        if data.get("post_timestamp") is not None and data.get("close_timestamp") is not None:
            if data["post_timestamp"] > data["close_timestamp"]:
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.INVALID,
                            "Post timestamp must be less than or equal to close timestamp",
                        )
                    ]
                )

    @validates_schema
    def set_archive_timestamp(self, data: dict, **kwargs: dict) -> None:
        if data.get("close_timestamp") is not None and (
            "archive_timestamp" not in data or data["archive_timestamp"] is None
        ):
            data["archive_timestamp"] = data["close_timestamp"] + timedelta(days=30)


class OpportunitySummaryCreateRequestSchema(OpportunitySummaryBaseRequestSchema):
    is_forecast = fields.Boolean(required=True)


class OpportunitySummaryUpdateRequestSchema(OpportunitySummaryBaseRequestSchema):
    pass


class OpportunitySummaryResponseSchema(AbstractResponseSchema):
    data = fields.Nested(OpportunitySummarySchema)


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

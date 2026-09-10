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
    AnnouncementCategory,
    ApplicantType,
    FundingCategory,
    FundingInstrument,
)
from src.pagination.pagination_schema import generate_pagination_schema


class AssistanceListingSchema(Schema):
    assistance_listing_id = fields.UUID()
    assistance_listing_number = fields.String()
    program_title = fields.String()


class AnnouncementAssistanceListingSchema(Schema):
    announcement_assistance_listing_id = fields.UUID()
    assistance_listing = fields.Nested(AssistanceListingSchema)


class AnnouncementSchema(Schema):
    announcement_id = fields.UUID()
    announcement_number = fields.String()
    announcement_title = fields.String()
    tagline = fields.String()
    purpose_statement = fields.String()
    category = fields.Enum(AnnouncementCategory, allow_none=True)
    category_explanation = fields.String(allow_none=True)

    announcement_assistance_listings = fields.List(
        fields.Nested(AnnouncementAssistanceListingSchema)
    )

    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class AnnouncementSummarySchema(Schema):
    announcement_summary_id = fields.UUID()
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
    estimated_award_timestamp = fields.DateTime(allow_none=True)
    estimated_project_start_timestamp = fields.DateTime(allow_none=True)
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


class AnnouncementSummaryBaseRequestSchema(Schema):
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
    estimated_award_timestamp = fields.DateTime(allow_none=True)
    estimated_project_start_timestamp = fields.DateTime(allow_none=True)
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
        # Preserve the existing Simpler behavior: archive 30 days after close when omitted.
        if data.get("close_timestamp") is not None and (
            "archive_timestamp" not in data or data["archive_timestamp"] is None
        ):
            data["archive_timestamp"] = data["close_timestamp"] + timedelta(days=30)


class AnnouncementSummaryCreateRequestSchema(AnnouncementSummaryBaseRequestSchema):
    is_forecast = fields.Boolean(required=True)


class AnnouncementSummaryUpdateRequestSchema(AnnouncementSummaryBaseRequestSchema):
    pass


class AnnouncementSummaryResponseSchema(AbstractResponseSchema):
    data = fields.Nested(AnnouncementSummarySchema)


class AnnouncementCreateRequestSchema(Schema):
    announcement_number = fields.String(
        required=True,
        validate=validators.Length(max=40),
    )
    announcement_title = fields.String(
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
    category = fields.Enum(AnnouncementCategory, required=True)
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
        if data.get("category") == AnnouncementCategory.OTHER:
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


class AnnouncementUpdateRequestSchema(Schema):
    announcement_title = fields.String(
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
    category = fields.Enum(AnnouncementCategory, required=True)
    category_explanation = fields.String(
        allow_none=True,
        load_default=None,
        validate=validators.Length(max=255),
    )

    @validates_schema
    def validate_category_explanation(self, data: dict, **kwargs: dict) -> None:
        if data.get("category") == AnnouncementCategory.OTHER:
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


class AnnouncementListFilterSchema(Schema):
    query = fields.String(
        allow_none=True,
        metadata={"description": "Case-insensitive search across announcement number and title"},
    )


class AnnouncementListRequestSchema(Schema):
    filters = fields.Nested(AnnouncementListFilterSchema())

    pagination = fields.Nested(
        generate_pagination_schema(
            "AnnouncementListPaginationSchema",
            [
                "announcement_id",
                "announcement_number",
                "announcement_title",
                "created_at",
            ],
            default_sort_order=[{"order_by": "created_at", "sort_direction": "descending"}],
            default_page_size=25,
            default_page_offset=1,
        ),
        required=True,
    )


class AnnouncementResponseSchema(AbstractResponseSchema):
    data = fields.Nested(AnnouncementSchema)


class AnnouncementListResponseSchema(AbstractResponseSchema, PaginationMixinSchema):
    data = fields.List(fields.Nested(AnnouncementSchema))

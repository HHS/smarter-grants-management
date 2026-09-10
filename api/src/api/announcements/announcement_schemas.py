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
    ApplicationPackageOpenToApplicant,
    FundingCategory,
    FundingInstrument,
)
from src.pagination.pagination_schema import generate_pagination_schema


class AnnouncementAssistanceListingSchema(Schema):
    announcement_assistance_listing_id = fields.UUID(
        metadata={"description": "The announcement assistance listing ID"}
    )

    assistance_listing_id = fields.UUID(
        metadata={"description": "The primary key ID of the assistance listing"}
    )
    program_title = fields.String(
        allow_none=True,
        metadata={
            "description": "The name of the program, see https://sam.gov/content/assistance-listings for more detail",
            "example": "Space Technology",
        },
    )
    assistance_listing_number = fields.String(
        allow_none=True,
        metadata={
            "description": "The assistance listing number, see https://sam.gov/content/assistance-listings for more detail",
            "example": "43.012",
        },
    )


class ApplicationPackageFormSchema(Schema):
    is_required = fields.Boolean(
        metadata={
            "description": "Whether the form is required for all applications to the application package"
        }
    )
    form_id = fields.Integer(
        metadata={"description": "The form this application package"},
    )


class ApplicationPackageSchema(Schema):
    application_package_id = fields.UUID(metadata={"description": "The application package ID"})

    announcement_id = fields.UUID(
        metadata={
            "description": "The announcement ID that the application package is associated with"
        }
    )

    application_package_forms = fields.List(
        fields.Nested(ApplicationPackageFormSchema()),
        metadata={"description": "List of forms required for this application package"},
    )

    # TODO - competition instructions when added

    public_application_package_id = fields.String(
        allow_none=True,
        metadata={
            "description": "The public-facing identifier of the application package",
            "example": "ABC-123-456",
        },
    )
    application_package_title = fields.String(
        allow_none=True,
        metadata={
            "description": "The title of the application package",
            "example": "Proposal for Advanced Research",
        },
    )
    opening_timestamp = fields.DateTime(
        allow_none=True,
        metadata={
            "description": "The opening date of the application package, the first day applications are accepted"
        },
    )
    closing_timestamp = fields.DateTime(
        allow_none=True,
        metadata={
            "description": "The closing date of the application package, the last day applications are accepted"
        },
    )
    grace_period = fields.Integer(
        allow_none=True,
        metadata={
            "description": "The number of days after the closing date that applications are still accepted",
            "example": 5,
        },
    )
    contact_info = fields.String(
        allow_none=True,
        metadata={
            "description": "Contact info getting assistance with the application package",
            "example": "Bob Smith\nFakeMail@fake.com",
        },
    )

    announcement_assistance_listing = fields.Nested(
        AnnouncementAssistanceListingSchema(),
        allow_none=True,
        metadata={"description": "Assistance listing information for this application package"},
    )

    open_to_applicants = fields.List(
        fields.Enum(ApplicationPackageOpenToApplicant),
        metadata={
            "description": "List of applicant types who are eligible for this application package",
            "example": [
                ApplicationPackageOpenToApplicant.INDIVIDUAL,
                ApplicationPackageOpenToApplicant.ORGANIZATION,
            ],
        },
    )


class AnnouncementSummarySchema(Schema):
    announcement_summary_id = fields.UUID(
        required=True,
        metadata={
            "description": "Unique identifier for the announcement summary",
        },
    )

    summary_description = fields.String(
        allow_none=True,
        metadata={
            "description": "The summary of the opportunity",
            "example": "This opportunity aims to unravel the mysteries of the universe.",
        },
    )
    is_cost_sharing = fields.Boolean(
        allow_none=True,
        metadata={
            "description": "Whether or not the opportunity has a cost sharing/matching requirement",
        },
    )
    is_forecast = fields.Boolean(
        metadata={
            "description": "Whether the announcement is forecasted, that is, the information is only an estimate and not yet official",
            "example": False,
        }
    )

    close_timestamp = fields.DateTime(
        allow_none=True,
        metadata={
            "description": "The date that the announcement will close - only set if is_forecast=False",
        },
    )
    close_timestamp_description = fields.String(
        allow_none=True,
        metadata={
            "description": "Optional details regarding the close date",
            "example": "Proposals are due earlier than usual.",
        },
    )

    post_timestamp = fields.DateTime(
        allow_none=True,
        metadata={
            "description": "The date the announcement was posted",
        },
    )
    archive_timestamp = fields.DateTime(
        allow_none=True,
        metadata={
            "description": "When the announcement will be archived",
        },
    )

    expected_number_of_awards = fields.Integer(
        allow_none=True,
        metadata={
            "description": "The number of awards the announcement is expected to award",
            "example": 10,
        },
    )
    estimated_total_program_funding = fields.Integer(
        allow_none=True,
        metadata={
            "description": "The total program funding of the announcement in US Dollars",
            "example": 10_000_000,
        },
    )
    award_floor = fields.Integer(
        allow_none=True,
        metadata={
            "description": "The minimum amount an announcement would award",
            "example": 10_000,
        },
    )
    award_ceiling = fields.Integer(
        allow_none=True,
        metadata={
            "description": "The maximum amount an announcement would award",
            "example": 100_000,
        },
    )

    additional_info_url = fields.String(
        allow_none=True,
        metadata={
            "description": "A URL to a website that can provide additional information about the announcement",
            "example": "grants.gov",
        },
    )
    additional_info_url_description = fields.String(
        allow_none=True,
        metadata={
            "description": "The text to display for the additional_info_url link",
            "example": "Click me for more info",
        },
    )

    forecasted_post_timestamp = fields.DateTime(
        allow_none=True,
        metadata={
            "description": "Forecasted announcement only. The date the announcement is expected to be posted, and transition out of being a forecast"
        },
    )
    forecasted_close_timestamp = fields.DateTime(
        allow_none=True,
        metadata={
            "description": "Forecasted announcement only. The date the announcement is expected to be close once posted."
        },
    )
    forecasted_close_timestamp_description = fields.String(
        allow_none=True,
        metadata={
            "description": "Forecasted announcement only. Optional details regarding the forecasted closed date.",
            "example": "Proposals will probably be due on this date",
        },
    )
    estimated_award_date = fields.Date(
        allow_none=True,
        metadata={"description": "The date the grantor plans to award the opportunity."},
    )
    estimated_project_start_date = fields.Date(
        allow_none=True,
        metadata={
            "description": "The date the grantor expects the award recipient should start their project"
        },
    )
    fiscal_year = fields.Integer(
        allow_none=True,
        metadata={
            "description": "The fiscal year the project is expected to be funded and launched"
        },
    )

    funding_category_description = fields.String(
        allow_none=True,
        metadata={
            "description": "Additional information about the funding category",
            "example": "Economic Support",
        },
    )
    applicant_eligibility_description = fields.String(
        allow_none=True,
        metadata={
            "description": "Additional information about the types of applicants that are eligible",
            "example": "All types of domestic applicants are eligible to apply",
        },
    )
    agency_contact_description = fields.String(
        allow_none=True,
        metadata={
            "description": "Information regarding contacting the agency who owns the opportunity",
            "example": "For more information, reach out to Jane Smith at agency US-ABC",
        },
    )
    agency_email_address = fields.String(
        allow_none=True,
        metadata={
            "description": "The contact email of the agency who owns the opportunity",
            "example": "fake_email@grants.gov",
        },
    )
    agency_email_address_description = fields.String(
        allow_none=True,
        metadata={
            "description": "The text for the link to the agency email address",
            "example": "Click me to email the agency",
        },
    )

    funding_instruments = fields.List(fields.Enum(FundingInstrument))
    funding_categories = fields.List(fields.Enum(FundingCategory))
    applicant_types = fields.List(fields.Enum(ApplicantType))

    created_at = fields.DateTime(
        metadata={"description": "When the opportunity summary was created"}
    )
    updated_at = fields.DateTime(
        metadata={"description": "When the opportunity summary was last updated"}
    )


class AnnouncementSchema(Schema):
    announcement_id = fields.UUID(metadata={"description": "The internal ID of the announcement"})
    announcement_number = fields.String(
        allow_none=True,
        metadata={"description": "The funding opportunity number", "example": "ABC-123-XYZ-001"},
    )
    announcement_title = fields.String(
        allow_none=True,
        metadata={
            "description": "The title of the announcement",
            "example": "Research into conservation techniques",
        },
    )
    tagline = fields.String(
        allow_none=True,
        metadata={
            "description": "A short tagline for the announcement",
            "example": "Accelerating climate innovation",
        },
    )
    purpose_statement = fields.String(
        allow_none=True,
        metadata={
            "description": "A brief statement describing the purpose of the announcement",
            "example": "Support research that advances innovative climate technologies.",
        },
    )
    category = fields.Enum(
        AnnouncementCategory,
        allow_none=True,
        metadata={
            "description": "The opportunity category",
            "example": AnnouncementCategory.DISCRETIONARY,
        },
    )
    category_explanation = fields.String(
        allow_none=True,
        metadata={
            "description": "Explanation of the category when the category is 'O' (other)",
            "example": None,
        },
    )

    announcement_assistance_listings = fields.List(
        fields.Nested(AnnouncementAssistanceListingSchema)
    )

    forecast_summary = fields.Nested(
        lambda: AnnouncementSummarySchema(),
        allow_none=True,
        attribute="forecast_summary",
        metadata={
            "description": "The forecast summary of the opportunity (if available)",
        },
    )

    non_forecast_summary = fields.Nested(
        lambda: AnnouncementSummarySchema(),
        allow_none=True,
        attribute="non_forecast_summary",
        metadata={
            "description": "The non-forecast summary of the opportunity (if available)",
        },
    )

    application_packages = fields.List(
        fields.Nested(ApplicationPackageSchema),
        metadata={"description": "List of application packages associated with the announcement"},
    )

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AnnouncementCreateRequestSchema(Schema):
    announcement_number = fields.String(
        required=True,
        validate=validators.Length(max=40),
        metadata={
            "description": "The funding opportunity number (must be unique)",
            "example": "ABC-2026-001",
        },
    )
    announcement_title = fields.String(
        required=True,
        validate=validators.Length(max=255),
        metadata={
            "description": "The title of the announcement",
            "example": "Research Grant for Climate Innovation",
        },
    )
    tagline = fields.String(
        required=True,
        validate=validators.Length(max=255),
        metadata={
            "description": "A short tagline for the announcement",
            "example": "Accelerating climate innovation",
        },
    )
    purpose_statement = fields.String(
        required=True,
        validate=validators.Length(max=255),
        metadata={
            "description": "A brief statement describing the purpose of the announcement",
            "example": "Support research that advances innovative climate technologies.",
        },
    )
    category = fields.Enum(
        AnnouncementCategory,
        required=True,
        metadata={
            "description": "The opportunity category",
        },
    )
    category_explanation = fields.String(
        allow_none=True,
        validate=validators.Length(max=255),
        metadata={
            "description": "Explanation of the category (required when category is 'other')",
            "example": "Competitive research grant",
        },
    )
    assistance_listing_number = fields.String(
        required=True,
        validate=validators.Length(max=6),
        metadata={
            "description": "The Assistance Listing Number",
            "example": "12.ABC",
        },
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
        metadata={
            "description": "The title of the announcement",
            "example": "Updated Research Grant for Climate Innovation",
        },
    )
    tagline = fields.String(
        required=True,
        validate=validators.Length(max=255),
        metadata={
            "description": "A short tagline for the announcement",
            "example": "Accelerating climate innovation",
        },
    )
    purpose_statement = fields.String(
        required=True,
        validate=validators.Length(max=255),
        metadata={
            "description": "A brief statement describing the purpose of the announcement",
            "example": "Support research that advances innovative climate technologies.",
        },
    )
    category = fields.Enum(
        AnnouncementCategory,
        required=True,
        metadata={
            "description": "The opportunity category",
        },
    )
    category_explanation = fields.String(
        allow_none=True,
        load_default=None,
        validate=validators.Length(max=255),
        metadata={
            "description": "Explanation of the category (required when category is 'other')",
        },
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


class AnnouncementListRequestSchema(Schema):

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

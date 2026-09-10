from marshmallow import ValidationError, validates_schema

from src.api.schemas.extension import (
    MarshmallowErrorContainer,
    Schema,
    SchemaValidationError,
    fields,
    validators,
)
from src.api.schemas.response_schema import AbstractResponseSchema, PaginationMixinSchema
from src.constants.lookup_constants import AnnouncementCategory
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

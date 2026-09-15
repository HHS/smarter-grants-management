from src.api.schemas.extension import Schema, fields
from src.api.schemas.response_schema import AbstractResponseSchema, PaginationMixinSchema
from src.pagination.pagination_schema import generate_pagination_schema


class AssistanceListingSearchRequestSchema(Schema):
    query = fields.String(
        metadata={
            "description": "Query string to filter results against the assistance listing number & program title",
            "example": "chem",
        },
    )

    pagination = fields.Nested(
        generate_pagination_schema(
            "AssistanceListingListPaginationSchema",
            [
                "program_title",
                "assistance_listing_number",
            ],
            default_sort_order=[
                {"order_by": "assistance_listing_number", "sort_direction": "ascending"}
            ],
        ),
        required=True,
    )


class AssistanceListingSchema(Schema):
    assistance_listing_id = fields.UUID(
        metadata={"description": "Unique ID of an assistance listing"}
    )

    assistance_listing_number = fields.String(
        metadata={
            "description": "The assistance listing number of the assistance listing",
            "example": "11.482",
        }
    )
    program_title = fields.String(
        metadata={
            "description": "The title of the assistance listing",
            "example": "Coral Reef Conservation Program",
        }
    )

    is_active = fields.Boolean(metadata={"description": "Whether the assistance listing is active"})
    published_date = fields.DateTime(
        metadata={"description": "The date the assistance listing was published / last updated"}
    )


class AssistanceListingSearchResponseSchema(AbstractResponseSchema, PaginationMixinSchema):
    data = fields.List(
        fields.Nested(AssistanceListingSchema),
        metadata={"description": "The list of assistance listings"},
    )

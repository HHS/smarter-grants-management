from apiflask import APIBlueprint

assistance_listing_blueprint = APIBlueprint(
    "assistance_listing",
    __name__,
    tag="Assistance Listing",
    cli_group="assistance_listing",
    url_prefix="/v1/assistance-listings",
)

from apiflask import APIBlueprint

opportunity_blueprint = APIBlueprint(
    "opportunity",
    __name__,
    tag="Opportunities",
    cli_group="opportunity",
    url_prefix="/v1/opportunities",
)

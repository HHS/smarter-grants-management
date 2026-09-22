from apiflask import APIBlueprint

internal_blueprint = APIBlueprint(
    "internal",
    __name__,
    tag="Internal",
    cli_group="internal",
    url_prefix="/v1/internal",
)

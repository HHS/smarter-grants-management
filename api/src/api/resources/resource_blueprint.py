from apiflask import APIBlueprint

resource_blueprint = APIBlueprint(
    "resources_v1",
    __name__,
    tag="Resources",
    cli_group="resources_v1",
    url_prefix="/v1/resources",
)

from apiflask import APIBlueprint

program_blueprint = APIBlueprint(
    "program",
    __name__,
    tag="Programs",
    cli_group="program",
    url_prefix="/v1/programs",
)

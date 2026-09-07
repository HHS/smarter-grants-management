from apiflask import APIBlueprint

file_blueprint = APIBlueprint(
    "files",
    __name__,
    tag="Files",
    cli_group="files",
    url_prefix="/v1/files",
)

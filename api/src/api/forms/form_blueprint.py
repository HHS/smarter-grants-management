from apiflask import APIBlueprint

form_blueprint = APIBlueprint(
    "form",
    __name__,
    tag="Forms",
    cli_group="form",
    url_prefix="/v1/forms",
)

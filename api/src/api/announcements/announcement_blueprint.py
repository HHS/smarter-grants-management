from apiflask import APIBlueprint

announcement_blueprint = APIBlueprint(
    "announcement",
    __name__,
    tag="Announcements",
    cli_group="announcement",
    url_prefix="/v1/announcements",
)

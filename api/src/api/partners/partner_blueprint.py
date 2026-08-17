from apiflask import APIBlueprint

partner_blueprint = APIBlueprint(
    "partner",
    __name__,
    tag="Partners",
    cli_group="partner",
    url_prefix="/v1/partners",
)

from apiflask import APIBlueprint

grantor_organization_blueprint = APIBlueprint(
    "grantor_organization",
    __name__,
    tag="Grantor Organizations",
    cli_group="grantor_organization",
    url_prefix="/v1/grantor-organizations",
)

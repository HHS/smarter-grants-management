from src.api.grantor_organizations.grantor_organization_blueprint import (
    grantor_organization_blueprint,
)

# import grantor_organization_routes module to register the API routes on the blueprint
import src.api.grantor_organizations.grantor_organization_routes  # ruff: ignore[unused-import] isort:skip

__all__ = ["grantor_organization_blueprint"]

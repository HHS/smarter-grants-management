from src.api.resources.resource_blueprint import resource_blueprint

# import resource_routes module to register the API routes on the blueprint
import src.api.resources.resource_routes  # ruff: ignore[unused-import] isort:skip

__all__ = ["resource_blueprint"]

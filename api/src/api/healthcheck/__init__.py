from src.api.healthcheck.healthcheck_blueprint import healthcheck_blueprint

# import healthcheck_routes module to register the API routes on the blueprint
import src.api.healthcheck.healthcheck_routes  # ruff: ignore[unused-import] isort:skip

__all__ = ["healthcheck_blueprint"]

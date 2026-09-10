from src.api.announcements.announcement_blueprint import announcement_blueprint

# import announcement_routes module to register the API routes on the blueprint
import src.api.announcements.announcement_routes  # ruff: ignore[unused-import] isort:skip

__all__ = ["announcement_blueprint"]

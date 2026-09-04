from src.task.task_blueprint import task_blueprint

# import any of the other files so they get initialized and attached to the blueprint
import src.task.dummy_task  # ruff: ignore[unused-import] isort:skip
import src.task.assistance_listing.fetch_assistance_listings  # ruff: ignore[unused-import] isort:skip

__all__ = ["task_blueprint"]

from src.api.programs.program_blueprint import program_blueprint

# import program_routes module to register the API routes on the blueprint
import src.api.programs.program_routes  # ruff: ignore[unused-import] isort:skip

__all__ = ["program_blueprint"]

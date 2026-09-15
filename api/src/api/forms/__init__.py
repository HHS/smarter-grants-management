from src.api.forms.form_blueprint import form_blueprint

# import form_routes module to register the API routes on the blueprint
import src.api.forms.form_routes  # ruff: ignore[unused-import] isort:skip

__all__ = ["form_blueprint"]

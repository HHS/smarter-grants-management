from src.api.partners.partner_blueprint import partner_blueprint

# import partner_routes module to register the API routes on the blueprint
import src.api.partners.partner_routes  # noqa: F401 isort:skip

__all__ = ["partner_blueprint"]

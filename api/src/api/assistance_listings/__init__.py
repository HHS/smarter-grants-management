from src.api.assistance_listings.assistance_listing_blueprint import assistance_listing_blueprint

# import assistance_listing_routes module to register the API routes on the blueprint
import src.api.assistance_listings.assistance_listing_routes  # ruff: ignore[unused-import] isort:skip

__all__ = ["assistance_listing_blueprint"]

from typing import Any

from src.db.models.user_models import User


def has_access(user: User, resource: Any, action: str) -> bool:
    """Temporary authorization seam for Opportunity functionality.

    The final Opportunity authorization model has not been decided yet.
    Replace this implementation once that design is finalized.
    """
    return True

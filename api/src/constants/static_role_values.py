# Our sync logic grabs this list to sync to the DB.
from src.db.models.resource_models import MgmtRole

CORE_ROLES: list[MgmtRole] = []

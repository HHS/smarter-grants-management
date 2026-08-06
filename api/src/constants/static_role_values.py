# Our sync logic grabs this list to sync to the DB.
from src.db.models.resource_models import MgmtRole

# TODO - https://github.com/HHS/simpler-grants-gov/issues/11827
#        will repopulate this list.
CORE_ROLES: list[MgmtRole] = []

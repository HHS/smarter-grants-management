import uuid

from src.constants.lookup_constants import Privilege, ResourceType
from src.db.models.resource_models import Role
from src.util.role_util import build_role

# Our sync logic grabs this list to sync to the DB.

PARTNER_ADMIN_ID = uuid.UUID("af2e7dfd-80b2-41c3-ac88-f6036b976469")
PARTNER_ADMIN = build_role(
    role_id=PARTNER_ADMIN_ID,
    role_name="Partner Admin",
    privileges={
        Privilege.VIEW_PARTNER,
        Privilege.MANAGE_PARTNER_MEMBERS,
        Privilege.UPDATE_PARTNER,
        Privilege.VIEW_PROGRAM,
        Privilege.UPDATE_PROGRAM,
        Privilege.VIEW_GRANTOR_ORGANIZATION,
        Privilege.UPDATE_GRANTOR_ORGANIZATION,
        Privilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS,
    },
    resource_types={ResourceType.PARTNER},
)

PARTNER_VIEWER_ID = uuid.UUID("5023853f-7a58-4aa3-9544-0ad39b1ded8d")
PARTNER_VIEWER = build_role(
    role_id=PARTNER_VIEWER_ID,
    role_name="Partner Viewer",
    privileges={
        Privilege.VIEW_PARTNER,
        Privilege.VIEW_PROGRAM,
        Privilege.VIEW_GRANTOR_ORGANIZATION,
    },
    resource_types={ResourceType.PARTNER},
)

GRANTOR_ORGANIZATION_ADMIN_ID = uuid.UUID("da5d1c66-ead3-4089-a3b8-8ce8dcaa188c")
GRANTOR_ORGANIZATION_ADMIN = build_role(
    role_id=GRANTOR_ORGANIZATION_ADMIN_ID,
    role_name="Grantor Organization Admin",
    privileges={
        Privilege.VIEW_PROGRAM,
        Privilege.UPDATE_PROGRAM,
        Privilege.VIEW_GRANTOR_ORGANIZATION,
        Privilege.UPDATE_GRANTOR_ORGANIZATION,
        Privilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS,
    },
    resource_types={ResourceType.GRANTOR_ORGANIZATION},
)

ORGANIZATION_VIEWER_ID = uuid.UUID("eb7daaa9-f107-41ce-b6b7-da1e451a0e12")
ORGANIZATION_VIEWER = build_role(
    role_id=ORGANIZATION_VIEWER_ID,
    role_name="Organization Viewer",
    privileges={
        Privilege.VIEW_PROGRAM,
        Privilege.VIEW_GRANTOR_ORGANIZATION,
    },
    resource_types={ResourceType.GRANTOR_ORGANIZATION},
)

CORE_ROLES: list[Role] = [
    PARTNER_ADMIN,
    PARTNER_VIEWER,
    GRANTOR_ORGANIZATION_ADMIN,
    ORGANIZATION_VIEWER,
]

"""The mapping from a resource type to the table that backs it.

Lives here rather than next to either of its callers because both the API's resource
endpoints and the workflow engine need it, and they sit in different packages. Keeping
one map means a new resource type becomes fetchable everywhere at once instead of
working in one place and quietly 404ing (or erroring) in the other.

Callers keep their own error handling - what a missing resource means differs by
context - so this deliberately exposes the mapping rather than a fetch-and-raise helper.
"""

from src.constants.lookup_constants import MgmtResourceType
from src.db.models.grantor_organization_models import GrantorOrganization, Partner, Program
from src.db.models.resource_models import AbstractResourceTableMixin, MgmtInternalResource

# A resource type absent from here has no table yet and isn't fetchable at all.
# MgmtResourceType.OPPORTUNITY is the current example - it's a valid resource type
# with no mgmt table behind it.
#
# Every resource-backed table uses its resource ID as its own primary key (see
# AbstractResourceTableMixin), so a plain `db_session.get(model, resource_id)` fetches
# any of them - no per-type ID column is needed.
RESOURCE_TYPE_TO_MODEL: dict[MgmtResourceType, type[AbstractResourceTableMixin]] = {
    MgmtResourceType.INTERNAL: MgmtInternalResource,
    MgmtResourceType.PARTNER: Partner,
    MgmtResourceType.GRANTOR_ORGANIZATION: GrantorOrganization,
    MgmtResourceType.PROGRAM: Program,
}


def get_resource_model(
    resource_type: MgmtResourceType,
) -> type[AbstractResourceTableMixin] | None:
    """Get the table backing a resource type, or None if it doesn't have one yet."""
    return RESOURCE_TYPE_TO_MODEL.get(resource_type)

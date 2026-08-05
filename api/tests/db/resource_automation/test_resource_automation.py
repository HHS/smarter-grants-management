import uuid

from sqlalchemy import select

from src.constants.lookup_constants import MgmtResourceType
from src.db.models.resource_models import MgmtInternalResource, MgmtResource
from tests.db.models.factories import MgmtInternalResourceFactory


def test_resource_automation_with_defaults(db_session):
    internal_resource = MgmtInternalResource(internal_resource_name="My example internal resource")
    db_session.add(internal_resource)

    db_session.commit()

    assert internal_resource.mgmt_internal_resource_id is not None
    assert (
        internal_resource.resource.mgmt_resource_id == internal_resource.mgmt_internal_resource_id
    )
    assert internal_resource.resource.mgmt_resource_type == MgmtResourceType.INTERNAL


def test_resource_automation_with_set_ids(db_session):

    internal_resource = MgmtInternalResource(
        mgmt_internal_resource_id=uuid.uuid4(),
        internal_resource_name="My example internal resource",
    )
    db_session.add(internal_resource)

    db_session.commit()

    assert internal_resource.mgmt_internal_resource_id is not None
    assert (
        internal_resource.resource.mgmt_resource_id == internal_resource.mgmt_internal_resource_id
    )
    assert internal_resource.resource.mgmt_resource_type == MgmtResourceType.INTERNAL


def test_resource_automation_does_not_change_resource_on_change(db_session, enable_factory_create):
    internal_resource_id = uuid.uuid4()
    internal_resource = MgmtInternalResourceFactory.create(
        mgmt_internal_resource_id=internal_resource_id
    )
    internal_resource.internal_resource_name = "New internal resource name"

    db_session.commit()

    db_session.refresh(internal_resource)
    assert internal_resource.mgmt_internal_resource_id == internal_resource_id
    assert internal_resource.resource.mgmt_resource_id == internal_resource_id
    assert internal_resource.internal_resource_name == "New internal resource name"


def test_resource_automation_when_deleting_resource(db_session, enable_factory_create):
    internal_resource = MgmtInternalResourceFactory.create()

    db_session.delete(internal_resource)
    db_session.commit()

    resources = db_session.execute(
        select(MgmtResource).where(
            MgmtResource.mgmt_resource_id.in_(
                [
                    internal_resource.mgmt_internal_resource_id,
                ]
            )
        )
    ).all()
    assert len(resources) == 0

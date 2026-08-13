import uuid

import pytest
from sqlalchemy import select

from src.auth.internal_resource import (
    INTERNAL_RESOURCE_NAME,
    create_internal_resource,
    get_internal_resource,
)
from src.constants.lookup_constants import ResourceType
from src.db.models.resource_models import InternalResource, Resource


@pytest.fixture
def internal_resource_id(monkeypatch):
    """Use a distinct configured internal resource ID per test so tests never collide."""
    internal_resource_id = uuid.uuid4()
    monkeypatch.setenv("INTERNAL_RESOURCE_ID", str(internal_resource_id))
    return internal_resource_id


def test_create_internal_resource(db_session, internal_resource_id):
    internal_resource = create_internal_resource(db_session)
    # Flush so the resource automation (before_flush) populates the backing resource row
    db_session.flush()

    assert internal_resource.internal_resource_id == internal_resource_id
    assert internal_resource.internal_resource_name == INTERNAL_RESOURCE_NAME

    # The backing resource row is created via resource automation
    assert internal_resource.resource.resource_id == internal_resource_id
    assert internal_resource.resource.resource_type == ResourceType.INTERNAL

    # Only a single record exists in the DB for the configured ID
    records = (
        db_session.execute(
            select(InternalResource).where(
                InternalResource.internal_resource_id == internal_resource_id
            )
        )
        .scalars()
        .all()
    )
    assert len(records) == 1


def test_create_internal_resource_is_idempotent(db_session, internal_resource_id):
    first = create_internal_resource(db_session)
    second = create_internal_resource(db_session)

    assert first.internal_resource_id == second.internal_resource_id == internal_resource_id

    # Still exactly one internal resource and one backing resource row for the configured ID
    internal_records = (
        db_session.execute(
            select(InternalResource).where(
                InternalResource.internal_resource_id == internal_resource_id
            )
        )
        .scalars()
        .all()
    )
    assert len(internal_records) == 1

    resource_records = (
        db_session.execute(select(Resource).where(Resource.resource_id == internal_resource_id))
        .scalars()
        .all()
    )
    assert len(resource_records) == 1


def test_get_internal_resource(db_session, internal_resource_id):
    created = create_internal_resource(db_session)

    fetched = get_internal_resource(db_session)

    assert fetched.internal_resource_id == created.internal_resource_id
    assert fetched.get_resource_id() == internal_resource_id
    assert fetched.get_resource_type() == ResourceType.INTERNAL


def test_get_internal_resource_raises_when_missing(db_session, internal_resource_id):
    with pytest.raises(ValueError, match="does not exist"):
        get_internal_resource(db_session)

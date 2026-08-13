import uuid

import pytest
from sqlalchemy import select

from src.db.migrations.setup_local_postgres_db import _create_internal_workflow_user
from src.db.models.user_models import MgmtUser


@pytest.fixture
def internal_workflow_user_id(monkeypatch):
    """Use a distinct configured user ID per test so tests never collide."""
    workflow_user_id = uuid.uuid4()
    monkeypatch.setenv("WORKFLOW_SERVICE_INTERNAL_USER_ID", str(workflow_user_id))
    return workflow_user_id


def test_create_internal_workflow_user(db_session, internal_workflow_user_id):
    workflow_user = _create_internal_workflow_user(db_session)
    db_session.flush()

    assert workflow_user.mgmt_user_id == internal_workflow_user_id
    assert (
        db_session.scalar(
            select(MgmtUser).where(MgmtUser.mgmt_user_id == internal_workflow_user_id)
        )
        is not None
    )


def test_create_internal_workflow_user_is_idempotent(db_session, internal_workflow_user_id):
    first = _create_internal_workflow_user(db_session)
    db_session.flush()

    second = _create_internal_workflow_user(db_session)
    db_session.flush()

    assert first.mgmt_user_id == second.mgmt_user_id
    users = list(
        db_session.execute(
            select(MgmtUser).where(MgmtUser.mgmt_user_id == internal_workflow_user_id)
        ).scalars()
    )
    assert len(users) == 1

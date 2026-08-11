import uuid

from sqlalchemy import select

from src.db.models.user_models import MgmtUser
from src.workflow.internal_workflow_user import create_internal_workflow_user


def test_create_internal_workflow_user(db_session, enable_factory_create, monkeypatch):
    user_id = uuid.uuid4()
    monkeypatch.setenv("WORKFLOW_SERVICE_INTERNAL_USER_ID", str(user_id))

    created = create_internal_workflow_user(db_session)
    db_session.commit()

    assert created.mgmt_user_id == user_id
    assert db_session.scalar(select(MgmtUser).where(MgmtUser.mgmt_user_id == user_id)) is not None


def test_create_internal_workflow_user_is_idempotent(
    db_session, enable_factory_create, monkeypatch
):
    user_id = uuid.uuid4()
    monkeypatch.setenv("WORKFLOW_SERVICE_INTERNAL_USER_ID", str(user_id))

    first = create_internal_workflow_user(db_session)
    db_session.commit()

    second = create_internal_workflow_user(db_session)
    db_session.commit()

    assert first.mgmt_user_id == second.mgmt_user_id
    users = list(
        db_session.execute(select(MgmtUser).where(MgmtUser.mgmt_user_id == user_id)).scalars()
    )
    assert len(users) == 1

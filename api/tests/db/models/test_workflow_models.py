import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.constants.lookup_constants import (
    MgmtApprovalResponseType,
    MgmtResourceType,
    MgmtWorkflowType,
)
from src.db.models.workflow_models import (
    MgmtWorkflow,
    MgmtWorkflowApproval,
    MgmtWorkflowAudit,
    MgmtWorkflowEventHistory,
)
from tests.db.models.factories import (
    MgmtInternalResourceFactory,
    MgmtWorkflowApprovalFactory,
    MgmtWorkflowAuditFactory,
    MgmtWorkflowEventHistoryFactory,
    MgmtWorkflowFactory,
)


def _fetch_workflow(db_session, workflow: MgmtWorkflow) -> MgmtWorkflow:
    db_session.expire_all()
    return db_session.execute(
        select(MgmtWorkflow).where(MgmtWorkflow.mgmt_workflow_id == workflow.mgmt_workflow_id)
    ).scalar_one()


def test_workflow_factory_build():
    workflow = MgmtWorkflowFactory.build()

    assert workflow.mgmt_workflow_id is not None
    assert workflow.workflow_type == MgmtWorkflowType.BASIC_TEST_WORKFLOW
    assert workflow.current_workflow_state == "start"
    assert workflow.is_active is True
    assert workflow.mgmt_resource_id == workflow.resource.mgmt_resource_id


def test_workflow_factory_create(enable_factory_create, db_session):
    workflow = MgmtWorkflowFactory.create()

    db_record = _fetch_workflow(db_session, workflow)

    assert db_record.workflow_type == MgmtWorkflowType.BASIC_TEST_WORKFLOW
    assert db_record.current_workflow_state == "start"
    assert db_record.is_active is True
    assert db_record.mgmt_resource_id == workflow.resource.mgmt_resource_id


def test_workflow_references_entity_through_its_resource(enable_factory_create, db_session):
    """A workflow attaches to an entity by pointing at that entity's resource row."""
    entity = MgmtInternalResourceFactory.create()

    workflow = MgmtWorkflowFactory.create(resource=entity.resource)

    db_record = _fetch_workflow(db_session, workflow)

    # The resource ID is the entity's own primary key, so the workflow gets back to
    # the entity without any per-entity FK column on the workflow table.
    assert db_record.mgmt_resource_id == entity.mgmt_internal_resource_id
    assert db_record.resource.mgmt_resource_type == MgmtResourceType.INTERNAL


def test_workflow_requires_a_resource(enable_factory_create, db_session):
    with pytest.raises(IntegrityError, match="mgmt_resource_id"):
        MgmtWorkflowFactory.create(resource=None, mgmt_resource_id=None)

    db_session.rollback()


def test_workflow_child_records(enable_factory_create, db_session):
    workflow = MgmtWorkflowFactory.create()

    event = MgmtWorkflowEventHistoryFactory.create(workflow=workflow)
    audit = MgmtWorkflowAuditFactory.create(workflow=workflow, event=event)
    approval = MgmtWorkflowApprovalFactory.create(workflow=workflow, event=event)

    db_record = _fetch_workflow(db_session, workflow)

    assert [e.mgmt_workflow_event_history_id for e in db_record.workflow_event_history] == [
        event.mgmt_workflow_event_history_id
    ]
    assert [a.mgmt_workflow_audit_id for a in db_record.workflow_audits] == [
        audit.mgmt_workflow_audit_id
    ]
    assert [a.mgmt_workflow_approval_id for a in db_record.workflow_approvals] == [
        approval.mgmt_workflow_approval_id
    ]

    assert db_record.workflow_audits[0].acting_user.mgmt_user_id == audit.acting_user.mgmt_user_id
    assert (
        db_record.workflow_approvals[0].approving_user.mgmt_user_id
        == approval.approving_user.mgmt_user_id
    )
    assert (
        db_record.workflow_approvals[0].approval_response_type == MgmtApprovalResponseType.APPROVED
    )


def test_deleting_workflow_deletes_child_records(enable_factory_create, db_session):
    workflow = MgmtWorkflowFactory.create()
    event = MgmtWorkflowEventHistoryFactory.create(workflow=workflow)
    audit = MgmtWorkflowAuditFactory.create(workflow=workflow, event=event)
    approval = MgmtWorkflowApprovalFactory.create(workflow=workflow, event=event)

    db_session.delete(_fetch_workflow(db_session, workflow))
    db_session.commit()

    assert db_session.get(MgmtWorkflow, workflow.mgmt_workflow_id) is None
    assert db_session.get(MgmtWorkflowEventHistory, event.mgmt_workflow_event_history_id) is None
    assert db_session.get(MgmtWorkflowAudit, audit.mgmt_workflow_audit_id) is None
    assert db_session.get(MgmtWorkflowApproval, approval.mgmt_workflow_approval_id) is None

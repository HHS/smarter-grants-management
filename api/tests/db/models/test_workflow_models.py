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
    MgmtWorkflowApprovalFactory,
    MgmtWorkflowAuditFactory,
    MgmtWorkflowEventHistoryFactory,
    ProgramFactory,
    ProgramWorkflowFactory,
)


def test_workflow_factory_build():
    workflow = ProgramWorkflowFactory.build()

    assert workflow.mgmt_workflow_id is not None
    assert workflow.workflow_type == MgmtWorkflowType.BASIC_TEST_WORKFLOW
    assert workflow.current_workflow_state == "start"
    assert workflow.is_active is True
    assert workflow.mgmt_resource_id is not None


def test_workflow_factory_create(enable_factory_create, db_session):
    workflow = ProgramWorkflowFactory.create()

    assert workflow.mgmt_workflow_id is not None
    assert workflow.workflow_type == MgmtWorkflowType.BASIC_TEST_WORKFLOW
    assert workflow.current_workflow_state == "start"
    assert workflow.is_active is True
    assert workflow.mgmt_resource_id is not None


def test_workflow_references_entity_through_its_resource(enable_factory_create, db_session):
    """A workflow attaches to an entity by pointing at that entity's resource row."""
    program = ProgramFactory.create()

    workflow = ProgramWorkflowFactory.create(program=program)

    # The factory only sets the resource ID, so fetch the resource itself from the DB.
    db_session.refresh(workflow)

    # The resource ID is the entity's own primary key, so the workflow gets back to
    # the entity without any per-entity FK column on the workflow table.
    assert workflow.mgmt_resource_id == program.program_id
    assert workflow.resource.mgmt_resource_type == MgmtResourceType.PROGRAM


def test_workflow_child_records(enable_factory_create, db_session):
    workflow = ProgramWorkflowFactory.create()

    event = MgmtWorkflowEventHistoryFactory.create(workflow=workflow)
    audit = MgmtWorkflowAuditFactory.create(workflow=workflow, event=event)
    approval = MgmtWorkflowApprovalFactory.create(workflow=workflow, event=event)

    # Load the child collections as the DB has them rather than as the factories
    # left them in memory, so this covers the foreign keys actually persisting.
    db_session.refresh(workflow)

    assert [e.mgmt_workflow_event_history_id for e in workflow.workflow_event_history] == [
        event.mgmt_workflow_event_history_id
    ]
    assert [a.mgmt_workflow_audit_id for a in workflow.workflow_audits] == [
        audit.mgmt_workflow_audit_id
    ]
    assert [a.mgmt_workflow_approval_id for a in workflow.workflow_approvals] == [
        approval.mgmt_workflow_approval_id
    ]

    assert workflow.workflow_audits[0].acting_user.mgmt_user_id == audit.acting_user.mgmt_user_id
    assert (
        workflow.workflow_approvals[0].approving_user.mgmt_user_id
        == approval.approving_user.mgmt_user_id
    )
    assert (
        workflow.workflow_approvals[0].approval_response_type == MgmtApprovalResponseType.APPROVED
    )


def test_deleting_workflow_deletes_child_records(enable_factory_create, db_session):
    workflow = ProgramWorkflowFactory.create()
    event = MgmtWorkflowEventHistoryFactory.create(workflow=workflow)
    audit = MgmtWorkflowAuditFactory.create(workflow=workflow, event=event)
    approval = MgmtWorkflowApprovalFactory.create(workflow=workflow, event=event)

    db_session.delete(workflow)
    db_session.commit()

    assert db_session.get(MgmtWorkflow, workflow.mgmt_workflow_id) is None
    assert db_session.get(MgmtWorkflowEventHistory, event.mgmt_workflow_event_history_id) is None
    assert db_session.get(MgmtWorkflowAudit, audit.mgmt_workflow_audit_id) is None
    assert db_session.get(MgmtWorkflowApproval, approval.mgmt_workflow_approval_id) is None

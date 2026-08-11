import pytest

from src.constants.lookup_constants import MgmtApprovalType, MgmtResourceType, MgmtWorkflowType
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel
from src.workflow.workflow_config import ApprovalConfig, WorkflowConfig


def test_workflow_config_cannot_have_duplicate_approval_states():
    with pytest.raises(
        Exception,
        match="Approval state pending_approval is configured on two separate approvals",
    ):
        WorkflowConfig(
            workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
            persistence_model_cls=BaseStatePersistenceModel,
            resource_type=MgmtResourceType.PROGRAM,
            approval_mapping={
                "receive_approval": ApprovalConfig(
                    approval_type=MgmtApprovalType.BASIC_TEST_APPROVAL,
                    approval_state="pending_approval",
                    required_privileges=[],
                ),
                "receive_approval_dupe": ApprovalConfig(
                    approval_type=MgmtApprovalType.BASIC_TEST_APPROVAL,
                    approval_state="pending_approval",
                    required_privileges=[],
                ),
            },
        )


def test_workflow_config_builds_state_approval_mapping():
    """The state -> approval mapping is derived from the event -> approval mapping."""
    approval_config = ApprovalConfig(
        approval_type=MgmtApprovalType.BASIC_TEST_APPROVAL,
        approval_state="pending_approval",
        required_privileges=[],
    )
    config = WorkflowConfig(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        persistence_model_cls=BaseStatePersistenceModel,
        resource_type=MgmtResourceType.PROGRAM,
        approval_mapping={"receive_approval": approval_config},
    )

    assert config.state_approval_mapping == {"pending_approval": approval_config}


def test_workflow_config_defaults_to_allowing_concurrent_workflows():
    config = WorkflowConfig(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        persistence_model_cls=BaseStatePersistenceModel,
        resource_type=MgmtResourceType.PROGRAM,
    )

    assert config.allow_concurrent_workflow_for_resource is True
    assert config.approval_mapping == {}
    assert config.state_approval_mapping == {}

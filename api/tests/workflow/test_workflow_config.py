import pytest

from src.constants.lookup_constants import ApprovalType, ResourceType, WorkflowType
from src.workflow.state_persistence.program_persistence_model import ProgramPersistenceModel
from src.workflow.workflow_config import ApprovalConfig, WorkflowConfig
from tests.workflow.workflow_test_util import PartnerTestPersistenceModel


def test_workflow_config_cannot_have_duplicate_approval_states():
    with pytest.raises(
        Exception,
        match="Approval state pending_approval is configured on two separate approvals",
    ):
        WorkflowConfig(
            workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
            persistence_model_cls=ProgramPersistenceModel,
            approval_mapping={
                "receive_approval": ApprovalConfig(
                    approval_type=ApprovalType.BASIC_TEST_APPROVAL,
                    approval_state="pending_approval",
                    required_privileges=[],
                ),
                "receive_approval_dupe": ApprovalConfig(
                    approval_type=ApprovalType.BASIC_TEST_APPROVAL,
                    approval_state="pending_approval",
                    required_privileges=[],
                ),
            },
        )


def test_workflow_config_builds_state_approval_mapping():
    """The state -> approval mapping is derived from the event -> approval mapping."""
    approval_config = ApprovalConfig(
        approval_type=ApprovalType.BASIC_TEST_APPROVAL,
        approval_state="pending_approval",
        required_privileges=[],
    )
    config = WorkflowConfig(
        workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
        persistence_model_cls=ProgramPersistenceModel,
        approval_mapping={"receive_approval": approval_config},
    )

    assert config.state_approval_mapping == {"pending_approval": approval_config}


def test_workflow_config_defaults():
    config = WorkflowConfig(
        workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
        persistence_model_cls=ProgramPersistenceModel,
    )

    assert config.allow_concurrent_workflow_for_resource is True
    assert config.approval_mapping == {}
    assert config.state_approval_mapping == {}


@pytest.mark.parametrize(
    "persistence_model_cls,expected_resource_type",
    [
        (ProgramPersistenceModel, ResourceType.PROGRAM),
        (PartnerTestPersistenceModel, ResourceType.PARTNER),
    ],
)
def test_workflow_config_resource_type_comes_from_the_persistence_model(
    persistence_model_cls, expected_resource_type
):
    """The resource type isn't configurable separately, so the two can't disagree."""
    config = WorkflowConfig(
        workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
        persistence_model_cls=persistence_model_cls,
    )

    assert config.resource_type == expected_resource_type

import dataclasses

from src.constants.lookup_constants import (
    MgmtApprovalResponseType,
    MgmtApprovalType,
    MgmtPrivilege,
    MgmtResourceType,
    MgmtWorkflowType,
)
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel


@dataclasses.dataclass
class ApprovalConfig:
    approval_type: MgmtApprovalType
    approval_state: str
    required_privileges: list[MgmtPrivilege]
    minimum_approvals_required: int = 1
    allowed_approval_response_types: set[MgmtApprovalResponseType] = dataclasses.field(
        default_factory=lambda: set(MgmtApprovalResponseType)
    )


@dataclasses.dataclass
class WorkflowConfig:

    workflow_type: MgmtWorkflowType

    persistence_model_cls: type[BaseStatePersistenceModel]

    # Whether to allow multiple active workflows of this type for the same resource.
    # When False, starting a new workflow will error if one already exists and is active.
    allow_concurrent_workflow_for_resource: bool = True

    # A mapping of events to approval configs
    approval_mapping: dict[str, ApprovalConfig] = dataclasses.field(default_factory=dict)

    # A mapping of states to approval configs
    # This is a slightly reoriented of the approval_mapping
    # and is automatically calculated in the post_init below.
    state_approval_mapping: dict[str, ApprovalConfig] = dataclasses.field(
        init=False, default_factory=dict
    )

    @property
    def resource_type(self) -> MgmtResourceType:
        """The type of resource a workflow of this type attaches to.

        Comes off the persistence model rather than being configured separately, so
        the two can't disagree. The engine resolves the resource from the event and
        checks its type against this, rather than trusting a type sent by the caller.
        """
        return self.persistence_model_cls.get_resource_type()

    def __post_init__(self) -> None:
        self.state_approval_mapping = {}

        for approval_config in self.approval_mapping.values():
            if approval_config.approval_state in self.state_approval_mapping:
                raise Exception(
                    f"Approval state {approval_config.approval_state} is configured on two separate approvals - must be unique"
                )

            self.state_approval_mapping[approval_config.approval_state] = approval_config

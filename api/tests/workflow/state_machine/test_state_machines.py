"""
This file contains state machines that only exist for our unit tests.

Testing core engine logic against a state machine defined here rather than against
the prototype (or, later, a real workflow) means these tests don't have to change
every time a real workflow does.
"""

from enum import StrEnum
from typing import Any

from statemachine import Event
from statemachine.states import States

from src.constants.lookup_constants import (
    ApprovalResponseType,
    ApprovalType,
    Privilege,
    WorkflowType,
)
from src.workflow.base_state_machine import BaseStateMachine
from src.workflow.event.state_machine_event import StateMachineEvent
from src.workflow.registry.workflow_registry import WorkflowRegistry
from src.workflow.state_persistence.base_state_persistence_model import BaseStatePersistenceModel
from src.workflow.state_persistence.program_persistence_model import ProgramPersistenceModel
from src.workflow.workflow_config import ApprovalConfig, WorkflowConfig
from src.workflow.workflow_constants import WorkflowConstants

#########################
# Basic State Machine
#########################
# A minimal start -> middle -> end workflow for exercising core engine behaviour.


class BasicState(StrEnum):
    START = "start"
    MIDDLE = "middle"
    END = "end"


basic_test_workflow_config = WorkflowConfig(
    workflow_type=WorkflowType.BASIC_TEST_WORKFLOW,
    persistence_model_cls=ProgramPersistenceModel,
    # Concurrent workflows are disallowed here so the engine's concurrency guard has a
    # registered workflow to test against. The prototype covers the allowed case, which
    # is the engine default.
    allow_concurrent_workflow_for_resource=False,
)


@WorkflowRegistry.register_workflow(basic_test_workflow_config)
class BasicTestStateMachine(BaseStateMachine):

    states = States.from_enum(
        BasicState,
        initial=BasicState.START,
        final=[BasicState.END],
    )

    ### Events + transitions
    start_workflow = Event(
        states.START.to(states.MIDDLE),
    )

    middle_to_end = Event(
        states.MIDDLE.to(states.END),
    )

    def __init__(self, model: BaseStatePersistenceModel, **kwargs: Any):
        super().__init__(model=model, **kwargs)

        # For testing purposes, store the transition events.
        self.transition_history: list[StateMachineEvent] = []

    def on_transition(self, state_machine_event: StateMachineEvent) -> None:
        self.transition_history.append(state_machine_event)


#########################
# Approval State Machine
#########################
# For testing the approval machinery. Neither the basic test machine nor
# the prototype configures approvals, so this covers approvals across two
# approval types with different privileges, plus a state requiring several
# approvals.
#
# The privileges here are existing program privileges rather than
# approval-specific ones - real approval privileges arrive with the real
# workflows that need them. What matters for these tests is only that the
# two approvals require different privileges, and that both are assignable
# on a program (and on the organizations above it, so the tests can pin
# what a parent-resource role does NOT get you).


class ApprovalState(StrEnum):
    START = "start"
    MIDDLE = "middle"

    PENDING_PRIMARY_APPROVAL = "pending_primary_approval"
    PENDING_SECONDARY_APPROVAL = "pending_secondary_approval"

    DECLINED = "declined"
    END = "end"


approval_test_workflow_config = WorkflowConfig(
    workflow_type=WorkflowType.APPROVAL_TEST_WORKFLOW,
    persistence_model_cls=ProgramPersistenceModel,
    approval_mapping={
        "receive_primary_approval": ApprovalConfig(
            approval_type=ApprovalType.BASIC_TEST_APPROVAL,
            approval_state=ApprovalState.PENDING_PRIMARY_APPROVAL,
            required_privileges=[Privilege.UPDATE_PROGRAM],
            minimum_approvals_required=3,  # require 3 approvals
        ),
        "receive_secondary_approval": ApprovalConfig(
            approval_type=ApprovalType.SECONDARY_TEST_APPROVAL,
            approval_state=ApprovalState.PENDING_SECONDARY_APPROVAL,
            required_privileges=[Privilege.VIEW_PROGRAM],
        ),
    },
)


@WorkflowRegistry.register_workflow(approval_test_workflow_config)
class ApprovalTestStateMachine(BaseStateMachine):

    states = States.from_enum(
        ApprovalState,
        initial=ApprovalState.START,
        final=[ApprovalState.END, ApprovalState.DECLINED],
    )

    ### Events + transitions
    start_workflow = Event(
        states.START.to(states.MIDDLE),
    )

    middle_to_end = Event(
        states.MIDDLE.to(states.END),
    )

    # These exist so we can test logic on entering approval states
    middle_to_primary_approval = Event(
        states.MIDDLE.to(states.PENDING_PRIMARY_APPROVAL),
    )

    middle_to_secondary_approval = Event(
        states.MIDDLE.to(states.PENDING_SECONDARY_APPROVAL),
    )

    ## Primary approvals
    receive_primary_approval = Event(
        # If Approved -> Add approval event and then check if enough approvals have occurred to determine next state
        states.PENDING_PRIMARY_APPROVAL.to.itself(
            cond=WorkflowConstants.IS_APPROVAL_EVENT_APPROVED,
            on=WorkflowConstants.ON_APPROVAL_APPROVED,
            after="check_primary_approval",
        )
        |
        # If Declined -> Add approval event and move to Declined state
        states.PENDING_PRIMARY_APPROVAL.to(
            states.DECLINED,
            cond=WorkflowConstants.IS_APPROVAL_EVENT_DECLINED,
            on=WorkflowConstants.ON_APPROVAL_DECLINED,
        )
        |
        # If Requires Modification -> Add approval event and move back to Start
        states.PENDING_PRIMARY_APPROVAL.to(
            states.START,
            cond=WorkflowConstants.IS_APPROVAL_EVENT_REQUIRES_MODIFICATION,
            on=WorkflowConstants.ON_APPROVAL_REQUIRES_MODIFICATION,
        )
    )

    check_primary_approval = Event(
        # If it has enough approvals, go to the End state
        states.PENDING_PRIMARY_APPROVAL.to(states.END, cond=WorkflowConstants.HAS_ENOUGH_APPROVALS)
        # If not, stay in this state
        | states.PENDING_PRIMARY_APPROVAL.to.itself(),
    )

    ## Secondary approvals
    receive_secondary_approval = Event(
        states.PENDING_SECONDARY_APPROVAL.to.itself(
            cond=WorkflowConstants.IS_APPROVAL_EVENT_APPROVED,
            on=WorkflowConstants.ON_APPROVAL_APPROVED,
            after="check_secondary_approval",
        )
        | states.PENDING_SECONDARY_APPROVAL.to(
            states.DECLINED,
            cond=WorkflowConstants.IS_APPROVAL_EVENT_DECLINED,
            on=WorkflowConstants.ON_APPROVAL_DECLINED,
        )
        | states.PENDING_SECONDARY_APPROVAL.to(
            states.START,
            cond=WorkflowConstants.IS_APPROVAL_EVENT_REQUIRES_MODIFICATION,
            on=WorkflowConstants.ON_APPROVAL_REQUIRES_MODIFICATION,
        )
    )

    check_secondary_approval = Event(
        states.PENDING_SECONDARY_APPROVAL.to(
            states.END, cond=WorkflowConstants.HAS_ENOUGH_APPROVALS
        )
        | states.PENDING_SECONDARY_APPROVAL.to.itself(),
    )

    def __init__(self, model: BaseStatePersistenceModel, **kwargs: Any):
        super().__init__(model=model, **kwargs)

        # For testing purposes, store the transition events.
        self.transition_history: list[StateMachineEvent] = []

    def on_transition(self, state_machine_event: StateMachineEvent) -> None:
        self.transition_history.append(state_machine_event)


#################################################
# Limited Approval Response Types State Machine
#################################################
# For testing that an approval config can restrict which response
# types it accepts. Same shape as the approval machine above, but
# each approval only allows a subset of the response types.


class LimitedApprovalResponseState(StrEnum):
    START = "start"
    MIDDLE = "middle"

    # Only allows APPROVED and REQUIRES_MODIFICATION
    PENDING_PRIMARY_APPROVAL = "pending_primary_approval"

    # Only allows APPROVED
    PENDING_SECONDARY_APPROVAL = "pending_secondary_approval"

    DECLINED = "declined"
    END = "end"


limited_approval_test_workflow_config = WorkflowConfig(
    workflow_type=WorkflowType.LIMITED_APPROVAL_TEST_WORKFLOW,
    persistence_model_cls=ProgramPersistenceModel,
    approval_mapping={
        "receive_primary_approval": ApprovalConfig(
            approval_type=ApprovalType.BASIC_TEST_APPROVAL,
            approval_state=LimitedApprovalResponseState.PENDING_PRIMARY_APPROVAL,
            required_privileges=[Privilege.UPDATE_PROGRAM],
            minimum_approvals_required=1,
            allowed_approval_response_types={
                ApprovalResponseType.APPROVED,
                ApprovalResponseType.REQUIRES_MODIFICATION,
            },
        ),
        "receive_secondary_approval": ApprovalConfig(
            approval_type=ApprovalType.SECONDARY_TEST_APPROVAL,
            approval_state=LimitedApprovalResponseState.PENDING_SECONDARY_APPROVAL,
            required_privileges=[Privilege.VIEW_PROGRAM],
            allowed_approval_response_types={ApprovalResponseType.APPROVED},
        ),
    },
)


@WorkflowRegistry.register_workflow(limited_approval_test_workflow_config)
class LimitedApprovalResponseStateMachine(BaseStateMachine):

    states = States.from_enum(
        LimitedApprovalResponseState,
        initial=LimitedApprovalResponseState.START,
        final=[LimitedApprovalResponseState.END, LimitedApprovalResponseState.DECLINED],
    )

    ### Events + transitions
    start_workflow = Event(
        states.START.to(states.MIDDLE),
    )

    middle_to_primary_approval = Event(
        states.MIDDLE.to(states.PENDING_PRIMARY_APPROVAL),
    )

    middle_to_secondary_approval = Event(
        states.MIDDLE.to(states.PENDING_SECONDARY_APPROVAL),
    )

    ## Primary approvals - declined is configured here, but not allowed by the
    ## approval config, so sending it errors before any transition happens.
    receive_primary_approval = Event(
        states.PENDING_PRIMARY_APPROVAL.to.itself(
            cond=WorkflowConstants.IS_APPROVAL_EVENT_APPROVED,
            on=WorkflowConstants.ON_APPROVAL_APPROVED,
            after="check_primary_approval",
        )
        | states.PENDING_PRIMARY_APPROVAL.to(
            states.DECLINED,
            cond=WorkflowConstants.IS_APPROVAL_EVENT_DECLINED,
            on=WorkflowConstants.ON_APPROVAL_DECLINED,
        )
        | states.PENDING_PRIMARY_APPROVAL.to(
            states.START,
            cond=WorkflowConstants.IS_APPROVAL_EVENT_REQUIRES_MODIFICATION,
            on=WorkflowConstants.ON_APPROVAL_REQUIRES_MODIFICATION,
        )
    )

    check_primary_approval = Event(
        states.PENDING_PRIMARY_APPROVAL.to(states.END, cond=WorkflowConstants.HAS_ENOUGH_APPROVALS)
        | states.PENDING_PRIMARY_APPROVAL.to.itself(),
    )

    ## Secondary approvals - only approved is allowed by the approval config
    receive_secondary_approval = Event(
        states.PENDING_SECONDARY_APPROVAL.to.itself(
            cond=WorkflowConstants.IS_APPROVAL_EVENT_APPROVED,
            on=WorkflowConstants.ON_APPROVAL_APPROVED,
            after="check_secondary_approval",
        )
        | states.PENDING_SECONDARY_APPROVAL.to(
            states.DECLINED,
            cond=WorkflowConstants.IS_APPROVAL_EVENT_DECLINED,
            on=WorkflowConstants.ON_APPROVAL_DECLINED,
        )
        | states.PENDING_SECONDARY_APPROVAL.to(
            states.START,
            cond=WorkflowConstants.IS_APPROVAL_EVENT_REQUIRES_MODIFICATION,
            on=WorkflowConstants.ON_APPROVAL_REQUIRES_MODIFICATION,
        )
    )

    check_secondary_approval = Event(
        states.PENDING_SECONDARY_APPROVAL.to(
            states.END, cond=WorkflowConstants.HAS_ENOUGH_APPROVALS
        )
        | states.PENDING_SECONDARY_APPROVAL.to.itself(),
    )

    def __init__(self, model: BaseStatePersistenceModel, **kwargs: Any):
        super().__init__(model=model, **kwargs)

        self.transition_history: list[StateMachineEvent] = []

    def on_transition(self, state_machine_event: StateMachineEvent) -> None:
        self.transition_history.append(state_machine_event)

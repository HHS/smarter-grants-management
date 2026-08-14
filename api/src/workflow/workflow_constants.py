class WorkflowConstants:
    START_WORKFLOW = "start_workflow"

    APPROVAL_RESPONSE_TYPE = "approval_response_type"
    COMMENT = "comment"

    # Common conditionals
    IS_APPROVAL_EVENT_APPROVED = "is_approval_event_approved"
    IS_APPROVAL_EVENT_DECLINED = "is_approval_event_declined"
    IS_APPROVAL_EVENT_REQUIRES_MODIFICATION = "is_approval_event_requires_modification"

    HAS_ENOUGH_APPROVALS = "has_enough_approvals"

    # Common "on" handlers
    # Note these are named for the approval rather than the approver - approvals here are
    # checked against a resource, and there are no agencies in this system.
    ON_APPROVAL_APPROVED = "on_approval_approved"
    ON_APPROVAL_DECLINED = "on_approval_declined"
    ON_APPROVAL_REQUIRES_MODIFICATION = "on_approval_requires_modification"

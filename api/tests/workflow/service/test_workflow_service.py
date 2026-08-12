import uuid

import pytest

from src.constants.lookup_constants import MgmtResourceType, MgmtWorkflowType
from src.db.models.resource_models import MgmtResource
from src.workflow.service.workflow_service import (
    get_and_validate_workflow,
    get_workflow_entity,
    is_event_valid_for_workflow,
    validate_no_concurrent_workflow,
)
from src.workflow.state_machine.prototype_state_machine import PrototypeStateMachine
from src.workflow.workflow_errors import (
    ConcurrentWorkflowError,
    EntityNotFound,
    ImplementationMissingError,
    InactiveWorkflowError,
    InvalidEntityForWorkflow,
    WorkflowDoesNotExistError,
)
from tests.db.models.factories import (
    GrantorOrganizationFactory,
    PartnerFactory,
    ProgramWorkflowFactory,
)
from tests.workflow.workflow_test_util import (
    GrantorOrganizationTestPersistenceModel,
    OpportunityTestPersistenceModel,
    PartnerTestPersistenceModel,
    build_workflow_config,
)

####################
# get_workflow_entity
####################


def test_get_workflow_entity_program(db_session, enable_factory_create, program):
    config = build_workflow_config()

    entity = get_workflow_entity(
        db_session,
        mgmt_resource_id=program.get_resource_id(),
        config=config,
    )

    assert entity is program
    assert entity.get_resource_id() == program.program_id


def test_get_workflow_entity_partner(db_session, enable_factory_create):
    partner = PartnerFactory.create()
    config = build_workflow_config(persistence_model_cls=PartnerTestPersistenceModel)

    entity = get_workflow_entity(
        db_session,
        mgmt_resource_id=partner.get_resource_id(),
        config=config,
    )

    assert entity is partner


def test_get_workflow_entity_grantor_organization(db_session, enable_factory_create):
    organization = GrantorOrganizationFactory.create()
    config = build_workflow_config(persistence_model_cls=GrantorOrganizationTestPersistenceModel)

    entity = get_workflow_entity(
        db_session,
        mgmt_resource_id=organization.get_resource_id(),
        config=config,
    )

    assert entity is organization


def test_get_workflow_entity_resource_missing(db_session, enable_factory_create):
    config = build_workflow_config()

    with pytest.raises(EntityNotFound, match="Resource not found"):
        get_workflow_entity(
            db_session,
            mgmt_resource_id=uuid.uuid4(),
            config=config,
        )


def test_get_workflow_entity_wrong_resource_type(db_session, enable_factory_create, program):
    """A resource of the wrong type for the workflow is rejected.

    The resource type comes off the resource row rather than the event, so a caller
    can't get a workflow attached to the wrong kind of entity by mislabeling it.
    """
    config = build_workflow_config(persistence_model_cls=PartnerTestPersistenceModel)

    with pytest.raises(
        InvalidEntityForWorkflow, match="Resource type does not match workflow configuration"
    ):
        get_workflow_entity(
            db_session,
            mgmt_resource_id=program.get_resource_id(),
            config=config,
        )


def test_get_workflow_entity_unsupported_resource_type(db_session, enable_factory_create):
    """A resource type with no table backing it in mgmt errors rather than resolving to nothing.

    OPPORTUNITY is a real resource type but has no mgmt table yet, so it's the case
    this covers - a workflow can't be configured against it until one exists.
    """
    config = build_workflow_config(persistence_model_cls=OpportunityTestPersistenceModel)
    resource = _create_bare_resource(db_session, MgmtResourceType.OPPORTUNITY)

    with pytest.raises(ImplementationMissingError, match="Resource type is not supported"):
        get_workflow_entity(
            db_session,
            mgmt_resource_id=resource.mgmt_resource_id,
            config=config,
        )


def test_get_workflow_entity_resource_without_entity(db_session, enable_factory_create):
    """A resource row whose backing entity row is missing errors rather than returning None.

    Resource automation creates the two together so this shouldn't happen, but it's
    the difference between a clear error and an AttributeError further downstream.
    """
    config = build_workflow_config()
    resource = _create_bare_resource(db_session, MgmtResourceType.PROGRAM)

    with pytest.raises(EntityNotFound, match="Resource has no corresponding entity"):
        get_workflow_entity(
            db_session,
            mgmt_resource_id=resource.mgmt_resource_id,
            config=config,
        )


def _create_bare_resource(db_session, resource_type: MgmtResourceType):
    """Create a resource row with no entity row behind it.

    Every resource-backed table creates its resource via the automation hook, so
    building one directly is the only way to reach the error paths above.
    """
    resource = MgmtResource(mgmt_resource_id=uuid.uuid4(), mgmt_resource_type=resource_type)
    db_session.add(resource)
    db_session.flush()
    return resource


####################
# is_event_valid_for_workflow
####################


@pytest.mark.parametrize(
    "event,expected_is_valid",
    [
        ("start_workflow", True),
        ("complete", True),
        ("finalize", True),
        ("fake_event", False),
        ("completeabc", False),
    ],
)
def test_is_event_valid_for_workflow(event, expected_is_valid):
    assert is_event_valid_for_workflow(event, PrototypeStateMachine) == expected_is_valid


####################
# get_and_validate_workflow
####################


def test_get_workflow(db_session, enable_factory_create):
    workflow = ProgramWorkflowFactory.create(workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW)

    fetched_workflow = get_and_validate_workflow(db_session, workflow.mgmt_workflow_id)
    assert fetched_workflow.mgmt_workflow_id == workflow.mgmt_workflow_id


def test_get_workflow_not_found(db_session):
    with pytest.raises(WorkflowDoesNotExistError, match="Workflow does not exist"):
        get_and_validate_workflow(db_session, uuid.uuid4())


def test_get_workflow_is_not_active(db_session, enable_factory_create):
    workflow = ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW, is_active=False
    )

    with pytest.raises(InactiveWorkflowError, match="Workflow is not active"):
        get_and_validate_workflow(db_session, workflow.mgmt_workflow_id)


####################
# validate_no_concurrent_workflow
####################


def test_validate_no_concurrent_workflow_allowed_by_config(
    db_session, enable_factory_create, program
):
    """When allow_concurrent_workflow_for_resource=True, no error is raised even if active workflow exists."""
    config = build_workflow_config(workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW)
    # Default is True, so this should be a no-op
    assert config.allow_concurrent_workflow_for_resource is True

    ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        program=program,
        is_active=True,
    )

    # Should not raise
    validate_no_concurrent_workflow(
        db_session,
        mgmt_resource_id=program.get_resource_id(),
        config=config,
    )


def test_validate_no_concurrent_workflow_errors_when_active_exists(
    db_session, enable_factory_create, program
):
    """When allow_concurrent_workflow_for_resource=False, should error if active workflow exists."""
    config = build_workflow_config(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        allow_concurrent_workflow_for_resource=False,
    )

    ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        program=program,
        is_active=True,
    )

    with pytest.raises(
        ConcurrentWorkflowError,
        match="An active workflow of this type already exists for this resource",
    ):
        validate_no_concurrent_workflow(
            db_session,
            mgmt_resource_id=program.get_resource_id(),
            config=config,
        )


def test_validate_no_concurrent_workflow_ok_when_inactive_exists(
    db_session, enable_factory_create, program
):
    """When allow_concurrent_workflow_for_resource=False, should NOT error if existing workflow is inactive."""
    config = build_workflow_config(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        allow_concurrent_workflow_for_resource=False,
    )

    ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        program=program,
        is_active=False,
    )

    # Should not raise since existing workflow is inactive
    validate_no_concurrent_workflow(
        db_session,
        mgmt_resource_id=program.get_resource_id(),
        config=config,
    )


def test_validate_no_concurrent_workflow_ok_when_no_workflow_exists(
    db_session, enable_factory_create, program
):
    """When allow_concurrent_workflow_for_resource=False, should NOT error if no workflow exists."""
    config = build_workflow_config(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        allow_concurrent_workflow_for_resource=False,
    )

    # No workflow created for this program
    validate_no_concurrent_workflow(
        db_session,
        mgmt_resource_id=program.get_resource_id(),
        config=config,
    )


def test_validate_no_concurrent_workflow_different_workflow_type(
    db_session, enable_factory_create, program
):
    """Active workflow of a different type should not block starting a new one."""
    config = build_workflow_config(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        allow_concurrent_workflow_for_resource=False,
    )

    # Create an active workflow of a DIFFERENT type
    ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.PROTOTYPE_WORKFLOW,
        program=program,
        is_active=True,
    )

    # Should not raise since the existing workflow is a different type
    validate_no_concurrent_workflow(
        db_session,
        mgmt_resource_id=program.get_resource_id(),
        config=config,
    )


def test_validate_no_concurrent_workflow_different_resource(
    db_session, enable_factory_create, program
):
    """An active workflow of the same type on another resource should not block this one."""
    config = build_workflow_config(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        allow_concurrent_workflow_for_resource=False,
    )

    # Active workflow of the same type, but hung off a different program
    ProgramWorkflowFactory.create(
        workflow_type=MgmtWorkflowType.BASIC_TEST_WORKFLOW,
        is_active=True,
    )

    validate_no_concurrent_workflow(
        db_session,
        mgmt_resource_id=program.get_resource_id(),
        config=config,
    )

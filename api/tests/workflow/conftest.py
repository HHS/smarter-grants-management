import pytest

from src.constants.lookup_constants import Privilege
from src.db.models.grantor_organization_models import Program
from src.db.models.user_models import User
from src.workflow.workflow_background_task import _init_newrelic_app
from tests.db.models.factories import ProgramFactory, UserFactory
from tests.workflow.workflow_test_util import create_approver

# The real state machines register themselves when src/workflow/state_machine is
# imported. Import the test-only ones here so they're registered for every workflow
# test rather than only the modules that happen to reference them directly.
import tests.workflow.state_machine.test_state_machines  # noqa: F401 isort:skip


@pytest.fixture(scope="session", autouse=True)
def init_new_relic_app():
    """Setup the new relic app to be initialized so the transaction logic
    won't error when running tests. This won't actually connect to New Relic.

    Outside of tests the workflow_background_task decorator does this, but that only
    runs for the CLI entry-point - anything calling into the manager directly needs it
    set up here or workflow_transaction raises.
    """
    _init_newrelic_app()


@pytest.fixture
def workflow_user(monkeypatch, enable_factory_create) -> User:
    """The internal user that automatic (engine-driven) state transitions are audited against.

    Points WORKFLOW_SERVICE_INTERNAL_USER_ID at a user that actually exists in the
    test schema - the audit record for an automatic transition sets the user ID
    without a lookup, so a missing user only surfaces as a foreign key error at
    commit time.
    """
    user = UserFactory.create()
    monkeypatch.setenv("WORKFLOW_SERVICE_INTERNAL_USER_ID", str(user.user_id))
    return user


@pytest.fixture(autouse=True)
def workflow_user_init(workflow_user):
    """Make the internal workflow user available to every workflow test."""


@pytest.fixture
def program(enable_factory_create) -> Program:
    """A program, which is what the prototype workflow attaches to.

    Programs are resource-backed, so the resource row the workflow points at is
    created for us by the resource automation flush hook.
    """
    return ProgramFactory.create()


@pytest.fixture
def primary_approver(db_session, program) -> User:
    """A user who can do the primary approval on a workflow attached to `program`.

    The role sits on the program's grant office because users are never attached to a
    program resource itself (see AuthorizationEnforcer._get_resources_for_program).
    """
    return create_approver(db_session, program.grant_office, privileges=[Privilege.UPDATE_PROGRAM])


@pytest.fixture
def secondary_approver(db_session, program) -> User:
    """A user who can do the secondary approval on a workflow attached to `program`."""
    return create_approver(db_session, program.program_office, privileges=[Privilege.VIEW_PROGRAM])


@pytest.fixture
def inherited_privilege_user(db_session, program) -> User:
    """A user whose approval privilege comes from the partner above the program.

    Approvals resolve approvers the same way the enforcer resolves access, so an
    inherited privilege is enough to approve - this fixture is what pins that.
    """
    return create_approver(db_session, program.partner, privileges=[Privilege.UPDATE_PROGRAM])

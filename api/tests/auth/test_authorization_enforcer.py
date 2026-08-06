import pytest
from apiflask import HTTPError

from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import MgmtPrivilege, MgmtResourceType
from tests.db.models.factories import MgmtInternalResourceFactory, MgmtRoleFactory, MgmtUserFactory
from tests.test_utils.auth_test_utils import setup_user_with_roles

######################################
# Resource Fixtures
######################################


@pytest.fixture
def internal_resource1(enable_factory_create):
    return MgmtInternalResourceFactory.create(internal_resource_name="Internal Resource 1")


@pytest.fixture
def internal_resource2(enable_factory_create):
    return MgmtInternalResourceFactory.create(internal_resource_name="Internal Resource 2")


######################################
# Tests
######################################


def test_user_with_no_roles_cannot_access_anything(
    db_session,
    # TODO - https://github.com/HHS/simpler-grants-gov/issues/11826
    #        add back all of the resource types
    internal_resource1,
    internal_resource2,
):
    user = MgmtUserFactory.create()

    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource1
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource2
        )
        is False
    )


def test_user_internal_resource(db_session, internal_resource1, internal_resource2):
    user = setup_user_with_roles(
        db_session,
        resources=[internal_resource1],
        privileges=[MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION],
    )

    # User can do VIEW_GRANTOR_ORGANIZATION against their internal resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource1
        )
        is True
    )
    # User cannot do another action against their internal resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION}, internal_resource1
        )
        is False
    )
    # User only has part of these privileges, so is denied
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user,
            {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION, MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION},
            internal_resource1,
        )
        is False
    )

    # User cannot view another internal resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource2
        )
        is False
    )


def test_user_with_multiple_privileges_in_role(db_session, internal_resource1, internal_resource2):
    user = setup_user_with_roles(
        db_session,
        resources=[internal_resource1],
        privileges=[
            MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION,
            MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION,
        ],
    )

    # User can view/update or both at the same time against their resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource1
        )
        is True
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION}, internal_resource1
        )
        is True
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user,
            {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION, MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION},
            internal_resource1,
        )
        is True
    )

    # Cannot do any other privileges, even with a partial overlap
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user,
            {
                MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION,
                MgmtPrivilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS,
            },
            internal_resource1,
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user,
            {
                MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION,
                MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION,
                MgmtPrivilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS,
            },
            internal_resource1,
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS}, internal_resource1
        )
        is False
    )

    # Cannot do those against another resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource2
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION}, internal_resource2
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user,
            {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION, MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION},
            internal_resource2,
        )
        is False
    )


def test_user_with_privileges_across_roles(db_session, internal_resource1, internal_resource2):
    """Same as test_user_with_multiple_privileges_in_role but the privilege is split across roles"""
    role1 = MgmtRoleFactory.create(
        privileges=[MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION],
        resource_types=[MgmtResourceType.INTERNAL],
    )
    role2 = MgmtRoleFactory.create(
        privileges=[MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION],
        resource_types=[MgmtResourceType.INTERNAL],
    )
    user = setup_user_with_roles(db_session, resources=[internal_resource1], roles=[role1, role2])

    # User can view/update or both at the same time against their resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource1
        )
        is True
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION}, internal_resource1
        )
        is True
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user,
            {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION, MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION},
            internal_resource1,
        )
        is True
    )

    # Cannot do any other privileges, even with a partial overlap
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user,
            {
                MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION,
                MgmtPrivilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS,
            },
            internal_resource1,
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user,
            {
                MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION,
                MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION,
                MgmtPrivilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS,
            },
            internal_resource1,
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.MANAGE_PARTNER_MEMBERS}, internal_resource1
        )
        is False
    )

    # Cannot do those against another resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource2
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION}, internal_resource2
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user,
            {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION, MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION},
            internal_resource2,
        )
        is False
    )


def test_verify_access(db_session, internal_resource1):
    user = MgmtUserFactory.create()
    with pytest.raises(HTTPError, match="Forbidden"):
        AuthorizationEnforcer(db_session).verify_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource1
        )

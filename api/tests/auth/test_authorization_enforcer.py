import pytest
from apiflask import HTTPError

from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import MgmtPrivilege, MgmtResourceType
from tests.db.models.factories import (
    GrantorOrganizationFactory,
    MgmtInternalResourceFactory,
    MgmtRoleFactory,
    MgmtUserFactory,
    PartnerFactory,
    ProgramFactory,
    SecondaryProgramPartnerFactory,
)
from tests.test_utils.auth_test_utils import setup_user_with_roles

######################################
# Resource Fixtures
######################################

# This is the hierarchy of the test data used in this file
# Programs connect to their organizations through dotted lines
#
# Partner                              A                      B
#                    ________________/  | \__________       /   \___________
#                   /    /              |            \      |              / \
#                  1    4 ..............|....         \     |             5    6
#                /  \     .             |   :          \    |            .    .
# Organization  2    3     .            |   :           \   |           ......
#               ..   :      .......     |   :            \  |          .
#                .   :             .    |   :             \ |         .
#                .   :              . /  \  :              \|        .
# Program        :... .............. X    Y                 Z .......
#                    :....................:

# Each program has a set of organizations as follows:
# Program X -> Program Office is Organization 2
#           -> Grant Office is Organization 4
#
# Program Y -> Program Office is Organization 3
#           -> Grant Office is Organization 4
#
# Program Z -> Program Office is Organization 5
#           -> Grant Office is Organization 6


@pytest.fixture
def partner_a(enable_factory_create):
    return PartnerFactory.create(partner_name="Partner A")


@pytest.fixture
def partner_b(enable_factory_create):
    return PartnerFactory.create(partner_name="Partner B")


@pytest.fixture
def organization_1(partner_a):
    return GrantorOrganizationFactory.create(organization_name="Organization 1", partner=partner_a)


@pytest.fixture
def organization_2(partner_a, organization_1):
    return GrantorOrganizationFactory.create(
        organization_name="Organization 2", partner=partner_a, parent_organization=organization_1
    )


@pytest.fixture
def organization_3(partner_a, organization_1):
    return GrantorOrganizationFactory.create(
        organization_name="Organization 3", partner=partner_a, parent_organization=organization_1
    )


@pytest.fixture
def organization_4(partner_a):
    return GrantorOrganizationFactory.create(organization_name="Organization 4", partner=partner_a)


@pytest.fixture
def organization_5(partner_b):
    return GrantorOrganizationFactory.create(organization_name="Organization 5", partner=partner_b)


@pytest.fixture
def organization_6(partner_b):
    return GrantorOrganizationFactory.create(organization_name="Organization 6", partner=partner_b)


@pytest.fixture
def program_x(partner_a, organization_2, organization_4):
    return ProgramFactory.create(
        program_name="Program X",
        partner=partner_a,
        program_office=organization_2,
        grant_office=organization_4,
    )


@pytest.fixture
def program_y(partner_a, organization_3, organization_4):
    return ProgramFactory.create(
        program_name="Program Y",
        partner=partner_a,
        program_office=organization_3,
        grant_office=organization_4,
    )


@pytest.fixture
def program_z(partner_a, partner_b, organization_5, organization_6):
    program = ProgramFactory.create(
        program_name="Program Z",
        partner=partner_b,
        program_office=organization_5,
        grant_office=organization_6,
        link_secondary_program_partners=[],
    )
    SecondaryProgramPartnerFactory.create(program=program, partner=partner_a)
    return program


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
    partner_a,
    partner_b,
    organization_1,
    organization_2,
    organization_3,
    organization_4,
    organization_5,
    organization_6,
    program_x,
    program_y,
    program_z,
    internal_resource1,
    internal_resource2,
):
    user = MgmtUserFactory.create()

    for resource in [
        partner_a,
        partner_b,
        organization_1,
        organization_2,
        organization_3,
        organization_4,
        organization_5,
        organization_6,
        program_x,
        program_y,
        program_z,
        internal_resource1,
        internal_resource2,
    ]:
        assert (
            AuthorizationEnforcer(db_session).can_access(
                user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, resource
            )
            is False
        )


def test_user_partner(
    db_session, partner_a, partner_b, program_x, organization_1, internal_resource1
):

    user = setup_user_with_roles(
        db_session, resources=[partner_a], privileges=[MgmtPrivilege.VIEW_PARTNER]
    )

    # User can view their partner
    assert (
        AuthorizationEnforcer(db_session).can_access(user, {MgmtPrivilege.VIEW_PARTNER}, partner_a)
        is True
    )

    # User does not have edit access on their partner
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.UPDATE_PARTNER}, partner_a
        )
        is False
    )

    # User cannot view another partner
    assert (
        AuthorizationEnforcer(db_session).can_access(user, {MgmtPrivilege.VIEW_PARTNER}, partner_b)
        is False
    )

    # While these aren't checks we'd realistically do,
    # if view_partner against an organization or program were asked,
    # a user could technically do it
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_PARTNER}, organization_1
        )
        is True
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(user, {MgmtPrivilege.VIEW_PARTNER}, program_x)
        is True
    )

    # No hierarchy gets to internal resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_PARTNER}, internal_resource1
        )
        is False
    )


def test_user_organization_parent_organization(
    db_session,
    organization_1,
    organization_2,
    organization_3,
    organization_4,
    partner_a,
    program_x,
    program_y,
    program_z,
    internal_resource1,
):
    user = setup_user_with_roles(
        db_session, resources=[organization_1], privileges=[MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION]
    )

    # User can view their organization
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, organization_1
        )
        is True
    )

    # User cannot edit their organization
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION}, organization_1
        )
        is False
    )

    # User cannot view against the partner
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, partner_a
        )
        is False
    )

    # User cannot view a different organization under the same partner
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, organization_4
        )
        is False
    )

    # User can view child organization
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, organization_2
        )
        is True
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, organization_3
        )
        is True
    )

    # User can view against program they're indirectly connected to (even if privilege doesn't make sense)
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, program_x
        )
        is True
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, program_y
        )
        is True
    )

    # This program is in a different hierarchy so there is no access
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, program_z
        )
        is False
    )

    # User cannot view internal resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource1
        )
        is False
    )


def test_user_organization_with_child_organization(
    db_session,
    organization_1,
    organization_2,
    organization_3,
    partner_a,
    program_x,
    program_y,
    program_z,
    internal_resource1,
):
    user = setup_user_with_roles(
        db_session, resources=[organization_2], privileges=[MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION]
    )

    # User can view their organization
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, organization_2
        )
        is True
    )

    # User cannot edit their organization
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.UPDATE_GRANTOR_ORGANIZATION}, organization_2
        )
        is False
    )

    # User cannot view against the partner
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, partner_a
        )
        is False
    )

    # User cannot view a different organization under the same partner
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, organization_3
        )
        is False
    )

    # User cannot view the parent organization
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, organization_1
        )
        is False
    )

    # User can view against program they're indirectly connected to (even if privilege doesn't make sense)
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, program_x
        )
        is True
    )

    # User cannot view program they are not connected to
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, program_y
        )
        is False
    )

    # This program is in a different hierarchy so there is no access
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, program_z
        )
        is False
    )

    # User cannot view internal resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, internal_resource1
        )
        is False
    )


def test_user_in_program_has_no_access(
    db_session,
    program_x,
    program_y,
    organization_2,
    organization_4,
    partner_a,
    partner_b,
    internal_resource1,
):
    """Test that users attached to a program don't get any access as this isn't an expected scenario"""
    user = setup_user_with_roles(
        db_session, resources=[program_x], privileges=[MgmtPrivilege.VIEW_PROGRAM]
    )

    # User cannot view their program
    # We do not add the program itself as a relevant resource so nothing can be found
    assert (
        AuthorizationEnforcer(db_session).can_access(user, {MgmtPrivilege.VIEW_PROGRAM}, program_x)
        is False
    )

    # User cannot edit their program
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.UPDATE_PROGRAM}, program_x
        )
        is False
    )

    # User cannot view_program against the organizations that owns it
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_PROGRAM}, organization_2
        )
        is False
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_PROGRAM}, organization_4
        )
        is False
    )

    # User cannot view_program against the partner that owns it
    assert (
        AuthorizationEnforcer(db_session).can_access(user, {MgmtPrivilege.VIEW_PROGRAM}, partner_a)
        is False
    )

    # User cannot view_program against a different program under the same partner
    assert (
        AuthorizationEnforcer(db_session).can_access(user, {MgmtPrivilege.VIEW_PROGRAM}, program_y)
        is False
    )

    # User cannot view_program against a program from a different partner
    assert (
        AuthorizationEnforcer(db_session).can_access(user, {MgmtPrivilege.VIEW_PROGRAM}, partner_b)
        is False
    )

    # User cannot view_program against any internal resource
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user, {MgmtPrivilege.VIEW_PROGRAM}, internal_resource1
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


def test_who_can_access_partner(
    db_session, partner_a, partner_b, organization_1, program_x, internal_resource1
):
    """Test that a given partner can only be accessed by a user attached to it"""

    # A user in the partner can access it.
    user_in_partner = setup_user_with_roles(
        db_session, resources=[partner_a], privileges=[MgmtPrivilege.VIEW_PARTNER]
    )
    assert (
        AuthorizationEnforcer(db_session).can_access(
            user_in_partner, {MgmtPrivilege.VIEW_PARTNER}, partner_a
        )
        is True
    )

    # A user in an organization attached to the partner cannot access it
    # A user in a program attached to the partner cannot access it
    # A user in another partner cannot access it
    # A user in an internal resource cannot access it
    for resource in [organization_1, program_x, partner_b, internal_resource1]:
        user_not_in_partner = setup_user_with_roles(
            db_session, resources=[resource], privileges=[MgmtPrivilege.VIEW_PARTNER]
        )
        assert (
            AuthorizationEnforcer(db_session).can_access(
                user_not_in_partner, {MgmtPrivilege.VIEW_PARTNER}, partner_a
            )
            is False
        )


def test_who_can_access_grantor_organization(
    db_session,
    organization_1,
    organization_2,
    organization_3,
    partner_a,
    partner_b,
    program_y,
    internal_resource1,
):
    """Test that for a given grantor organization, who can access it"""

    # A user in the organization can view it
    # A user in the parent organization can view it
    # A user in the partner that owns the organization can view it
    for resource in [organization_3, organization_1, partner_a]:
        user_who_can_access = setup_user_with_roles(
            db_session, resources=[resource], privileges=[MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION]
        )
        assert (
            AuthorizationEnforcer(db_session).can_access(
                user_who_can_access, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, organization_3
            )
            is True
        )

    # A user in a different organization, but same partner cannot view it
    # A user in a program connected to the organization cannot view it
    # A user in a different partner cannot view it
    # A user in an internal resource cannot access it
    for resource in [organization_2, program_y, partner_b, internal_resource1]:
        user_who_cannot_access = setup_user_with_roles(
            db_session, resources=[resource], privileges=[MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION]
        )
        assert (
            AuthorizationEnforcer(db_session).can_access(
                user_who_cannot_access, {MgmtPrivilege.VIEW_GRANTOR_ORGANIZATION}, organization_3
            )
            is False
        )


def test_who_can_access_program(
    db_session,
    program_x,
    program_y,
    partner_a,
    partner_b,
    organization_1,
    organization_2,
    organization_3,
    organization_4,
    internal_resource1,
):
    """Test that for a given program, who can access it."""

    # A user in the partner that owns the program can view it
    # A user in the organizations that own it can access it
    # A user in the parent of the organizations that own it can access it
    for resource in [partner_a, organization_3, organization_4, organization_1]:
        user_who_can_access = setup_user_with_roles(
            db_session, resources=[resource], privileges=[MgmtPrivilege.VIEW_PROGRAM]
        )
        assert (
            AuthorizationEnforcer(db_session).can_access(
                user_who_can_access, {MgmtPrivilege.VIEW_PROGRAM}, program_y
            )
            is True
        )

    # A user in the program cannot access it (membership in a program gives no access and is not checked)
    # A user in an organization in the same partner, but not an owner, cannot access it
    # A user in a different partner cannot access it
    # A user in a different program cannot access it
    # A user in an internal resource cannot access it
    for resource in [program_y, organization_2, partner_b, program_x, internal_resource1]:
        user_who_cannot_access = setup_user_with_roles(
            db_session, resources=[resource], privileges=[MgmtPrivilege.VIEW_PROGRAM]
        )
        assert (
            AuthorizationEnforcer(db_session).can_access(
                user_who_cannot_access, {MgmtPrivilege.VIEW_PROGRAM}, program_y
            )
            is False
        )


def test_who_can_access_program_with_secondary_partner(
    db_session,
    program_x,
    program_y,
    program_z,
    partner_a,
    partner_b,
    organization_2,
    organization_5,
    organization_6,
    internal_resource1,
):
    """Test that for a given program, who can access it if it has secondary partners"""

    # A user in the partner that owns the program can view it
    # A user in the secondary partner can view it
    # A user in the organizations that own it can access it
    for resource in [partner_b, partner_a, organization_5, organization_6]:
        user_who_can_access = setup_user_with_roles(
            db_session, resources=[resource], privileges=[MgmtPrivilege.VIEW_PROGRAM]
        )
        assert (
            AuthorizationEnforcer(db_session).can_access(
                user_who_can_access, {MgmtPrivilege.VIEW_PROGRAM}, program_z
            )
            is True
        )

    # A user in the program cannot access it (membership in a program gives no access and is not checked)
    # A user in an organization from a different partner cannot access it
    # A user in a different program cannot access it
    # A user in an internal resource cannot access it
    for resource in [program_z, organization_2, program_x, internal_resource1]:
        user_who_cannot_access = setup_user_with_roles(
            db_session, resources=[resource], privileges=[MgmtPrivilege.VIEW_PROGRAM]
        )
        assert (
            AuthorizationEnforcer(db_session).can_access(
                user_who_cannot_access, {MgmtPrivilege.VIEW_PROGRAM}, program_z
            )
            is False
        )

import pytest
from apiflask import HTTPError

from src.auth.authorization_enforcer import AuthorizationEnforcer
from src.constants.lookup_constants import MgmtPrivilege, MgmtResourceType
from src.db.models.grantor_organization_models import GrantorOrganization
from tests.db.models.factories import MgmtInternalResourceFactory, MgmtRoleFactory, MgmtUserFactory, PartnerFactory, \
    GrantorOrganizationFactory, ProgramFactory, SecondaryProgramPartnerFactory
from tests.test_utils.auth_test_utils import setup_user_with_roles

######################################
# Resource Fixtures
######################################

# This is the hierarchy of the test data used in this file (NOTE - orgs connection to program described below)
#
# Partner                              A                     B
#                    ________________/  | \__________        |   \___________
#                   /    /              |            \      |              / \
#                  1    4               |             \     |             5    6
#                /  \                   |              \    |
# Organization  2    3                  |               \   |
#                                       |                \  |
#                                       |                 \ |
#                                     /  \                 \|
# Program                            X    Y                 Z
#
#

# Additionally, each program has a set of organizations as follows:
# Program X -> Program Office is Organization 2
#           -> Grant Office is Organization 4
#
# Program Y -> Program Office is Organization 3
#           -> Grant Office is Organization 4
#
# Program Z -> Program Office is Organization 5
#           -> Grant Office is Organization 6

# TODO - make all these scoped to the module

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
    return GrantorOrganizationFactory.create(organization_name="Organization 2", partner=partner_a, parent_organization=organization_1)

@pytest.fixture
def organization_3(partner_a, organization_1):
    return GrantorOrganizationFactory.create(organization_name="Organization 3", partner=partner_a, parent_organization=organization_1)

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
    return ProgramFactory.create(program_name="Program X", partner=partner_a, program_office=organization_2, grant_office=organization_4)

@pytest.fixture
def program_y(partner_a, organization_3, organization_4):
    return ProgramFactory.create(program_name="Program Y", partner=partner_a, program_office=organization_3, grant_office=organization_4)

@pytest.fixture
def program_z(partner_a, partner_b, organization_5, organization_6):
    program = ProgramFactory.create(program_name="Program Z", partner=partner_b, program_office=organization_5, grant_office=organization_6, link_secondary_program_partners=[])
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




# TODO

###  Partner access
# Only accessed by exactly the partner
# Cannot be accessed by any program/org under it

### Org access
# Can be accessed by the org itself
# Can be accessed by the owning partner
# Can be accessed by the parent org
# Cannot be accessed by another partner
# Cannot be accessed by another org in the hierarchy


### Program access
# Can be accessed by the partner owning it
# Can be accessed by the secondary partner
# Can be accessed by the two orgs that own it
# Can be accessed by the two orgs that own it or their parents
# Cannot be accessed by another program
# Cannot be accessed by a non-secondary partner

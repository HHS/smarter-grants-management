import random
from datetime import datetime

import factory
import factory.fuzzy
import faker
from faker.providers import BaseProvider
from sqlalchemy.orm import scoped_session

import src.adapters.db as db
import src.db.models.announcement_models as announcement_models
import src.db.models.application_package_models as application_package_models
import src.db.models.assistance_listing_models as assistance_listing_models
import src.db.models.file_upload_models as file_upload_models
import src.db.models.grantor_organization_models as grantor_organization_models
import src.db.models.resource_models as resource_models
import src.db.models.user_models as user_models
import src.db.models.workflow_models as workflow_models
from src.constants.lookup_constants import (
    AnnouncementCategory,
    ApplicantType,
    ApplicationPackageOpenToApplicant,
    ApprovalResponseType,
    ApprovalType,
    ExternalUserType,
    FileScanStatus,
    FormFamily,
    FundingCategory,
    FundingInstrument,
    GrantorOrganizationAuditEvent,
    GrantorOrganizationType,
    PartnerAuditEvent,
    ResourceType,
    UserType,
    WorkflowType,
)
from src.util import datetime_util
from tests.db_test_models import db_test_models


def sometimes_none(factory_value, none_chance: float = 0.5):
    return factory.Maybe(
        decider=factory.LazyAttribute(lambda s: random.random() > none_chance),
        yes_declaration=factory_value,
        no_declaration=None,
    )


class CustomProvider(BaseProvider):
    """
    This class is a custom faker provider that can be used to generate
    fake data for our specific scenarios.

    The name of the functions defined in this class is the name of the individual provider.
    For example, the "agency_code" method below can be called by doing either of the following::

        fake.agency_code()

        factory.Faker("agency_code")

    Below we register this provider class with both the faker instance we setup, as well as
    the underlying one backing the factory's faker instance.

    See: https://faker.readthedocs.io/en/master/#how-to-create-a-provider
    """

    # Various words we can use when building the department names
    # Stuff that sounds like it might be an department, even if its not exactly the name
    DEPARTMENT_WORDS = [
        "Agriculture",
        "Commerce",
        "Defense",
        "Education",
        "Economics",
        "Energy",
        "Health",
        "Housing",
        "Justice",
        "Labor",
        "State",
        "Interior",
        "Transportation",
        "Science",
        "Arts",
    ]

    DEPARTMENT_NAME_FORMATS = [
        "Department of {{department_word}}",
        "Department of the {{department_word}}",
        "Agency for {{department_word}}",
        "National {{department_word}} Administration",
    ]

    # Various words associated with agencies
    AGENCY_WORDS = [
        "Health",
        "Global Affairs",
        "Human Development",
        "Intergovernmental Affairs",
        "Healthcare",
        "Medicare",
        "Disease Control",
        "Disease Prevention",
        "Consumer Affairs",
        "Tax Policy",
        "Management",
        "Legislative Affairs",
        "Aviation",
        "Highway",
        "Railroad",
        "Inspector General",
        "Intelligence",
        "Labor",
        "Civil Rights",
        "Antitrust",
        "Attorney General",
        "Housing",
        "American",
        "Chemistry",
        "Physics",
        "Biology",
        "Commerce",
        "Science",
        "Social Services",
        "Development Fund",
        "Regional Operations",
        "Ocean",
    ]

    SUBAGENCY_NAME_FORMATS = [
        "Center for {{agency_word}}",
        "Agency for {{agency_word}}",
        "Administration for {{agency_word}} and {{agency_word}}",
        "Center for Advanced {{agency_word}} Research",
        "{{agency_word}} and {{agency_word}} Administration",
        "{{agency_word}} Service",
        "Office of {{agency_word}}",
        "Office of {{agency_word}} for {{agency_word}}",
        "National Institute on {{agency_word}}",
        "Bureau of {{agency_word}}",
    ]

    GRANT_OFFICE_NAME_FORMATS = [
        "{{department_name}} - Grant Office",
        "{{agency_word}} Headquarters - Grant Office",
    ]

    PROGRAM_NAME_FORMATS = [
        "{{agency_word}} Program",
        "{{agency_word}} Research",
        "{{agency_word}}'s Bureau",
        "{{agency_word}}",
        "Office of {{agency_word}}",
        "{{agency_word}} Safety",
        "Statewide {{agency_word}} & {{agency_word}}",
        "{{agency_word}} Title {{random_int}}",
        "{{agency_word}} Act",
    ]

    ASSISTANCE_LISTING_NUMBER_FORMATS = ["##.???", "##.###"]

    AGENCY_CONTACT_DESC_FORMATS = [
        "{{name}}\n{{job}}\n555-###-####\n{{email}}",
        "{{relevant_url}} Contact Center\nHours of operation are 24 hours a day, 7 days a week.\n{{email}}",
        "Webmaster\n{{email}}",
    ]

    # Rather than generate any random URL in our data, use those
    # that are vaguely relevant to avoid linking to anything outside
    # of the grants ecosystem that could cause confusion in test data
    # (ie. either a website we work with, or a very generic one)
    RELEVANT_URLS = ["google.com", "grants.gov", "simpler.grants.gov", "sam.gov"]

    ADDITIONAL_INFO_DESC_FORMATS = [
        "Full Announcement",
        "Grants.gov",
        "Link to grant on {{relevant_url}}",
        "Program Announcement",
        "Click on the link to see the full announcement.",
        "Division of {{company}}",
    ]

    # This is to help with the unique agency code conflicts
    AGENCY_CODE_FORMATS = [
        # We don't make anything of format ???
        # To avoid overlap with real agencies as we
        # saw tests just happen to match exactly
        # and get a unique constraint issue
        "FAKE???",
        "????",
        "???-??",
        "???-???",
        "???-???-##",
        "???-???-???-##",
        "???-??-##-??",
    ]

    # Opportunity title uses several other existing providers
    # to generate titles. Anything in {{ }} is calling a provider
    # with that name.
    OPPORTUNITY_TITLE_FORMATS = [
        "Research into {{job}} industry",
        "Embassy program for {{job}} in {{country}}",
        "{{name}} Foundation Grant for {{bs}}",
        "{{company}} {{year}} award",
    ]

    SUMMARY_DESCRIPTION_FORMATS = [
        "{{agency_code}} is looking to further investigate this topic. {{paragraph}}",
        "<p>{{paragraph}}</p><p><br></p><p>{{paragraph}}</p>",
        "The purpose of this Notice of Funding Opportunity (NOFO) is to support research into {{job}} and how we might {{catch_phrase}}.",
        "<div>{{paragraph:long}} <a href='{{relevant_url}}'>{{sentence}}</a> {{paragraph:long}}</div> <div>{{paragraph:long}} <a href='{{relevant_url}}'>{{sentence}}</a> {{paragraph:long}}</div>",
    ]

    # In the formatting, ? becomes a random letter, # becomes a random digit
    OPPORTUNITY_NUMBER_FORMATS = [
        "???-###-FY{{year}}-###",
        "{{agency_code}}-##-###",
        "???#######",
        "??-##-???-###",
        "{{word}}-###-##",
    ]

    def department_word(self) -> str:
        return self.random_element(self.DEPARTMENT_WORDS)

    def department_name(self) -> str:
        pattern = self.random_element(self.DEPARTMENT_NAME_FORMATS)
        return self.generator.parse(pattern)

    def agency_word(self) -> str:
        return self.random_element(self.AGENCY_WORDS)

    def subagency_name(self) -> str:
        pattern = self.random_element(self.SUBAGENCY_NAME_FORMATS)
        return self.generator.parse(pattern)

    def grant_office_name(self) -> str:
        pattern = self.random_element(self.GRANT_OFFICE_NAME_FORMATS)
        return self.generator.parse(pattern)

    def program_name(self) -> str:
        pattern = self.random_element(self.PROGRAM_NAME_FORMATS)
        return self.generator.parse(pattern)

    def agency_code(self) -> str:
        pattern = self.bothify(self.random_element(self.AGENCY_CODE_FORMATS)).upper()
        return self.generator.parse(pattern)

    def assistance_listing_number(self) -> str:
        pattern = self.bothify(self.random_element(self.ASSISTANCE_LISTING_NUMBER_FORMATS)).upper()
        return self.generator.parse(pattern)

    def opportunity_number(self) -> str:
        # bothify turns any ? into letters, and # into digits
        pattern = self.bothify(self.random_element(self.OPPORTUNITY_NUMBER_FORMATS))
        return self.generator.parse(pattern).upper()

    def opportunity_title(self) -> str:
        pattern = self.random_element(self.OPPORTUNITY_TITLE_FORMATS)
        return self.generator.parse(pattern)

    def summary_description(self) -> str:
        self.generator.set_arguments("long", {"nb_sentences": 25})
        pattern = self.random_element(self.SUMMARY_DESCRIPTION_FORMATS)
        return self.generator.parse(pattern)

    def relevant_url(self):
        return self.random_element(self.RELEVANT_URLS)

    def additional_info_desc(self):
        pattern = self.random_element(self.ADDITIONAL_INFO_DESC_FORMATS)
        return self.generator.parse(pattern)

    def agency_contact_description(self) -> str:
        # bothify turns any ? into letters, and # into digits
        pattern = self.bothify(self.random_element(self.AGENCY_CONTACT_DESC_FORMATS))
        return self.generator.parse(pattern)


fake = faker.Faker()
fake.add_provider(CustomProvider)
factory.Faker.add_provider(CustomProvider)

_db_session: db.Session | None = None


def get_db_session() -> db.Session:
    # _db_session is only set in the pytest fixture `enable_factory_create`
    # so that tests do not unintentionally write to the database.
    if _db_session is None:
        raise Exception("""Factory db_session is not initialized.

            If your tests don't need to cover database behavior, consider
            calling the `build()` method instead of `create()` on the factory to
            not persist the generated model.

            If running tests that actually need data in the DB, pull in the
            `enable_factory_create` fixture to initialize the db_session.
            """)

    return _db_session


class Generators:
    Now = factory.LazyFunction(datetime.now)
    UtcNow = factory.LazyFunction(datetime_util.utcnow)
    UuidObj = factory.Faker("uuid4", cast_to=None)
    PhoneNumber = factory.Sequence(lambda n: f"123-456-{n:04}")


# The scopefunc ensures that the session gets cleaned up after each test
# it implicitly calls `remove()` on the session.
# see https://docs.sqlalchemy.org/en/20/orm/contextual.html
Session = scoped_session(lambda: get_db_session(), scopefunc=lambda: get_db_session())


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):

    class Meta:
        abstract = True
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "commit"


###################
# User & Auth Factories
###################


class UserFactory(BaseFactory):
    class Meta:
        model = user_models.User

    user_id = Generators.UuidObj
    user_type = UserType.STANDARD


class LinkExternalUserFactory(BaseFactory):
    class Meta:
        model = user_models.LinkExternalUser

    link_external_user_id = Generators.UuidObj
    external_user_id = Generators.UuidObj

    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda s: s.user.user_id)

    external_user_type = factory.fuzzy.FuzzyChoice(ExternalUserType)

    email = factory.Faker("email")


class LoginGovStateFactory(BaseFactory):
    class Meta:
        model = user_models.LoginGovState

    login_gov_state_id = Generators.UuidObj
    nonce = Generators.UuidObj


class UserTokenSessionFactory(BaseFactory):
    class Meta:
        model = user_models.UserTokenSession

    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda s: s.user.user_id)

    token_id = Generators.UuidObj

    expires_at = factory.Faker("date_time_between", start_date="+1d", end_date="+10d")

    is_valid = True


class InternalResourceFactory(BaseFactory):
    class Meta:
        model = resource_models.InternalResource

    internal_resource_id = Generators.UuidObj
    internal_resource_name = "My internal resource"


class PartnerFactory(BaseFactory):
    class Meta:
        model = grantor_organization_models.Partner

    partner_id = Generators.UuidObj

    partner_name = factory.Faker("department_name")


class GrantorOrganizationFactory(BaseFactory):
    class Meta:
        model = grantor_organization_models.GrantorOrganization

    grantor_organization_id = Generators.UuidObj

    organization_name = factory.Maybe(
        decider=factory.LazyAttribute(
            lambda o: o.grantor_organization_type == GrantorOrganizationType.GRANT_OFFICE
        ),
        yes_declaration=factory.Faker("grant_office_name"),
        no_declaration=factory.Faker("subagency_name"),
    )

    partner = factory.SubFactory(PartnerFactory)
    partner_id = factory.LazyAttribute(lambda o: o.partner.partner_id)

    # A parent organization can be set either manually
    # or using the trait below.
    parent_organization = None
    parent_organization_id = factory.LazyAttribute(
        lambda o: o.parent_organization.grantor_organization_id if o.parent_organization else None
    )

    grantor_organization_type = factory.fuzzy.FuzzyChoice(GrantorOrganizationType)

    class Params:
        pass
        has_parent_organization = factory.Trait(
            parent_organization=factory.SubFactory(
                "tests.db.models.factories.GrantorOrganizationFactory",
                # Make sure it has the same partner
                partner=factory.SelfAttribute("..partner"),
            ),
        )


class PartnerAuditFactory(BaseFactory):
    class Meta:
        model = grantor_organization_models.PartnerAudit

    partner_audit_id = Generators.UuidObj

    partner = factory.SubFactory(PartnerFactory)
    partner_id = factory.LazyAttribute(lambda a: a.partner.partner_id)

    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda a: a.user.user_id)

    partner_audit_event = PartnerAuditEvent.USER_ROLES_MODIFIED

    target_user = sometimes_none(factory.SubFactory(UserFactory), none_chance=0.5)
    target_user_id = factory.LazyAttribute(
        lambda a: a.target_user.user_id if a.target_user else None
    )

    audit_metadata = sometimes_none(factory.LazyAttribute(lambda x: {}), none_chance=0.5)


class GrantorOrganizationAuditFactory(BaseFactory):
    class Meta:
        model = grantor_organization_models.GrantorOrganizationAudit

    grantor_organization_audit_id = Generators.UuidObj

    grantor_organization = factory.SubFactory(GrantorOrganizationFactory)
    grantor_organization_id = factory.LazyAttribute(
        lambda a: a.grantor_organization.grantor_organization_id
    )

    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda a: a.user.user_id)

    grantor_organization_audit_event = GrantorOrganizationAuditEvent.USER_ROLES_MODIFIED

    target_user = sometimes_none(factory.SubFactory(UserFactory), none_chance=0.5)
    target_user_id = factory.LazyAttribute(
        lambda a: a.target_user.user_id if a.target_user else None
    )

    audit_metadata = sometimes_none(factory.LazyAttribute(lambda x: {}), none_chance=0.5)


class ProgramFactory(BaseFactory):
    class Meta:
        model = grantor_organization_models.Program

    program_id = Generators.UuidObj

    program_name = factory.Faker("program_name")

    partner = factory.SubFactory(PartnerFactory)
    partner_id = factory.LazyAttribute(lambda p: p.partner.partner_id)

    program_office = factory.SubFactory(
        GrantorOrganizationFactory,
        grantor_organization_type=GrantorOrganizationType.PROGRAM_OFFICE,
        partner=factory.SelfAttribute("..partner"),
    )
    program_office_id = factory.LazyAttribute(lambda p: p.program_office.grantor_organization_id)

    grant_office = factory.SubFactory(
        GrantorOrganizationFactory,
        grantor_organization_type=GrantorOrganizationType.GRANT_OFFICE,
        partner=factory.SelfAttribute("..partner"),
    )
    grant_office_id = factory.LazyAttribute(lambda p: p.grant_office.grantor_organization_id)

    class Params:
        has_secondary_partners = factory.Trait(
            link_secondary_program_partners=factory.RelatedFactoryList(
                "tests.db.models.factories.SecondaryProgramPartnerFactory",
                factory_related_name="program",
                size=lambda: random.randint(1, 3),
            )
        )


class SecondaryProgramPartnerFactory(BaseFactory):
    class Meta:
        model = grantor_organization_models.SecondaryProgramPartner

    partner = factory.SubFactory(PartnerFactory)
    partner_id = factory.LazyAttribute(lambda s: s.partner.partner_id)

    program = factory.SubFactory(ProgramFactory)
    program_id = factory.LazyAttribute(lambda s: s.program.program_id)


class RoleFactory(BaseFactory):
    class Meta:
        model = resource_models.Role

    role_id = Generators.UuidObj
    role_name = factory.Faker("sentence", nb_words=3)
    is_core = False

    resource_types = [ResourceType.INTERNAL]
    privileges = []


class ResourceFactory(BaseFactory):
    class Meta:
        model = resource_models.Resource

    resource_id = Generators.UuidObj

    resource_type = factory.fuzzy.FuzzyChoice(ResourceType)


class ResourceUserFactory(BaseFactory):
    class Meta:
        model = resource_models.ResourceUser

    resource_user_id = Generators.UuidObj

    resource = factory.SubFactory(ResourceFactory)
    resource_id = factory.LazyAttribute(lambda r: r.resource.resource_id)

    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda r: r.user.user_id)


class ResourceUserRoleFactory(BaseFactory):
    class Meta:
        model = resource_models.ResourceUserRole

    resource_user = factory.SubFactory(ResourceUserFactory)
    resource_user_id = factory.LazyAttribute(lambda r: r.resource_user.resource_user_id)

    role = factory.SubFactory(RoleFactory)
    role_id = factory.LazyAttribute(lambda r: r.role.role_id)


class UserApiKeyFactory(BaseFactory):
    class Meta:
        model = user_models.UserApiKey

    api_key_id = Generators.UuidObj
    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda s: s.user.user_id)

    key_name = factory.Faker("sentence", nb_words=3)
    key_id = factory.Sequence(lambda n: f"aws-api-gateway-key-{n:08d}")

    last_used = sometimes_none(
        factory.Faker("date_time_between", start_date="-30d", end_date="now"), none_chance=0.3
    )
    is_active = True

    class Params:
        # Trait for inactive keys
        inactive = factory.Trait(is_active=False)

        # Trait for recently used keys
        recently_used = factory.Trait(
            last_used=factory.Faker("date_time_between", start_date="-7d", end_date="now")
        )

        # Trait for unused keys
        never_used = factory.Trait(last_used=None)


###################
# Workflow Factories
###################


class WorkflowFactory(BaseFactory):
    """
    Base factory for workflows - abstract because every workflow points at some
    entity's resource, and which entity that is depends on the workflow.

    Add a subclass per entity a workflow can attach to (see ProgramWorkflowFactory)
    rather than using this directly.
    """

    class Meta:
        # Deliberately no model here - subclasses set it. If the model were set on
        # both, factory_boy would share one sequence counter between parent and
        # child, and reset_sequence() on the child raises (see test_seed_local_db).
        abstract = True

    workflow_id = Generators.UuidObj
    workflow_type = WorkflowType.BASIC_TEST_WORKFLOW
    current_workflow_state = "start"
    is_active = True


class ProgramWorkflowFactory(WorkflowFactory):
    """A workflow attached to a program. Pass `program=` to use an existing one."""

    class Meta:
        model = workflow_models.Workflow
        # The program is what we hang the workflow off of, but the workflow
        # itself only stores the resource ID, so don't pass it to the model.
        exclude = ("program",)

    program = factory.SubFactory(ProgramFactory)
    resource_id = factory.LazyAttribute(lambda w: w.program.get_resource_id())


class WorkflowEventHistoryFactory(BaseFactory):
    class Meta:
        model = workflow_models.WorkflowEventHistory

    workflow_event_history_id = Generators.UuidObj
    event_data = {}
    sent_at = Generators.UtcNow
    is_successfully_processed = True


class WorkflowAuditFactory(BaseFactory):
    class Meta:
        model = workflow_models.WorkflowAudit

    workflow_audit_id = Generators.UuidObj

    workflow = factory.SubFactory(ProgramWorkflowFactory)
    workflow_id = factory.LazyAttribute(lambda a: a.workflow.workflow_id)

    acting_user = factory.SubFactory(UserFactory)
    acting_user_id = factory.LazyAttribute(lambda a: a.acting_user.user_id)

    transition_event = "process"
    source_state = "start"
    target_state = "end"

    event = factory.SubFactory(WorkflowEventHistoryFactory)
    workflow_event_history_id = factory.LazyAttribute(lambda a: a.event.workflow_event_history_id)


class WorkflowApprovalFactory(BaseFactory):
    class Meta:
        model = workflow_models.WorkflowApproval

    workflow_approval_id = Generators.UuidObj

    workflow = factory.SubFactory(ProgramWorkflowFactory)
    workflow_id = factory.LazyAttribute(lambda a: a.workflow.workflow_id)

    approving_user = factory.SubFactory(UserFactory)
    approving_user_id = factory.LazyAttribute(lambda a: a.approving_user.user_id)

    approval_type = factory.fuzzy.FuzzyChoice(ApprovalType)
    is_still_valid = True
    approval_response_type = ApprovalResponseType.APPROVED

    event = factory.SubFactory(WorkflowEventHistoryFactory)
    workflow_event_history_id = factory.LazyAttribute(lambda a: a.event.workflow_event_history_id)


class AssistanceListingFactory(BaseFactory):
    class Meta:
        model = assistance_listing_models.AssistanceListing

    assistance_listing_id = Generators.UuidObj

    program_title = factory.Faker("program_name")
    assistance_listing_number = factory.LazyFunction(
        lambda: fake.unique.assistance_listing_number()
    )

    is_active = True

    published_date = factory.Faker("date_time_between", start_date="-5y", end_date="now")


###################
# Announcement Factories
###################


class AnnouncementFactory(BaseFactory):
    class Meta:
        model = announcement_models.Announcement

    announcement_id = Generators.UuidObj

    announcement_number = factory.Faker("opportunity_number")
    announcement_title = factory.Faker("opportunity_title")

    category = factory.fuzzy.FuzzyChoice(AnnouncementCategory)
    # only set the category explanation if category is Other
    category_explanation = factory.Maybe(
        decider=factory.LazyAttribute(lambda o: o.category == AnnouncementCategory.OTHER),
        yes_declaration=factory.Faker("sentence", nb_words=3),
        no_declaration=None,
    )

    tagline = factory.Faker("sentence")
    purpose_statement = factory.Faker("paragraph")

    announcement_assistance_listings = factory.RelatedFactoryList(
        "tests.db.models.factories.AnnouncementAssistanceListingFactory",
        factory_related_name="announcement",
        size=lambda: random.randint(1, 2),
    )


class AnnouncementAssistanceListingFactory(BaseFactory):
    class Meta:
        model = announcement_models.AnnouncementAssistanceListing

    announcement_assistance_listing_id = Generators.UuidObj

    announcement = factory.SubFactory(AnnouncementFactory)
    announcement_id = factory.LazyAttribute(lambda a: a.announcement.announcement_id)

    assistance_listing = factory.SubFactory(AssistanceListingFactory)
    assistance_listing_id = factory.LazyAttribute(
        lambda a: a.assistance_listing.assistance_listing_id
    )


class AnnouncementSummaryFactory(BaseFactory):
    class Meta:
        model = announcement_models.AnnouncementSummary

    announcement_summary_id = Generators.UuidObj

    announcement = factory.SubFactory(AnnouncementFactory)
    announcement_id = factory.LazyAttribute(lambda a: a.announcement.announcement_id)

    summary_description = factory.Faker("summary_description")
    is_cost_sharing = factory.Faker("boolean")

    # By default generate non-forecasts which affects several fields
    is_forecast = False

    # Forecasted records don't have a close date
    close_timestamp = factory.Maybe(
        decider=factory.LazyAttribute(lambda s: s.is_forecast),
        # If forecasted, don't set a close date
        yes_declaration=None,
        # otherwise a future date
        no_declaration=factory.Faker("date_time_between", start_date="+2w", end_date="+3w"),
    )
    close_timestamp_description = factory.Maybe(
        decider=factory.LazyAttribute(lambda s: s.close_timestamp is None),
        yes_declaration=None,
        no_declaration=factory.Faker("paragraph", nb_sentences=1),
    )

    # Just a random recent post time
    post_timestamp = factory.Faker("date_time_between", start_date="-3w", end_date="-1d")

    # By default set to a time in the future
    archive_timestamp = factory.Faker("date_time_between", start_date="+3w", end_date="+4w")

    expected_number_of_awards = factory.Faker("random_int", min=1, max=25)
    estimated_total_program_funding = factory.Faker(
        "random_int", min=10_000, max=10_000_000, step=5_000
    )
    award_floor = factory.LazyAttribute(
        lambda s: s.estimated_total_program_funding // s.expected_number_of_awards
    )
    award_ceiling = factory.LazyAttribute(lambda s: s.estimated_total_program_funding)

    additional_info_url = factory.Faker("relevant_url")
    additional_info_url_description = factory.Faker("additional_info_desc")

    # Forecasted values are only set if is_forecast=True
    forecasted_post_timestamp = factory.Maybe(
        decider=factory.LazyAttribute(lambda s: s.is_forecast),
        # If forecasted, set it in the future
        yes_declaration=factory.Faker("date_time_between", start_date="+2w", end_date="+3w"),
        # otherwise don't set
        no_declaration=None,
    )
    forecasted_close_timestamp = factory.Maybe(
        decider=factory.LazyAttribute(lambda s: s.is_forecast),
        # If forecasted, set it in the future
        yes_declaration=factory.Faker("date_time_between", start_date="+6w", end_date="+12w"),
        # otherwise don't set
        no_declaration=None,
    )
    forecasted_close_timestamp_description = factory.Maybe(
        decider=factory.LazyAttribute(lambda s: s.forecasted_close_timestamp is None),
        yes_declaration=None,
        no_declaration=factory.Faker("paragraph", nb_sentences=1),
    )

    estimated_award_date = sometimes_none(
        factory.Faker("date_between", start_date="+26w", end_date="+30w")
    )
    estimated_project_start_date = sometimes_none(
        factory.Faker("date_between", start_date="+30w", end_date="+52w")
    )

    fiscal_year = factory.LazyAttribute(
        lambda s: s.estimated_project_start_date.year if s.estimated_project_start_date else None
    )

    funding_category_description = sometimes_none(factory.Faker("paragraph", nb_sentences=1))
    applicant_eligibility_description = sometimes_none(factory.Faker("paragraph", nb_sentences=1))

    agency_contact_description = factory.Faker("agency_contact_description")
    agency_email_address = factory.Faker("email")
    agency_email_address_description = factory.LazyAttribute(
        lambda s: "Contact this agency via email"
    )

    funding_instruments = factory.Faker(
        "random_elements",
        length=random.randint(1, 3),
        elements=[f for f in FundingInstrument],
        unique=True,
    )
    funding_categories = factory.Faker(
        "random_elements",
        length=random.randint(1, 3),
        elements=[f for f in FundingCategory],
        unique=True,
    )
    applicant_types = factory.Faker(
        "random_elements",
        length=random.randint(1, 3),
        elements=[a for a in ApplicantType],
        unique=True,
    )


class ApplicationPackageFactory(BaseFactory):
    class Meta:
        model = application_package_models.ApplicationPackage

    application_package_id = Generators.UuidObj

    announcement = factory.SubFactory(AnnouncementFactory)
    announcement_id = factory.LazyAttribute(lambda a: a.announcement.announcement_id)

    form_family = factory.fuzzy.FuzzyChoice(FormFamily)

    public_application_package_id = sometimes_none("ABC-134-56789")

    application_package_title = sometimes_none(factory.Faker("sentence"))

    opening_timestamp = factory.Faker("date_time_between", start_date="-3w", end_date="-1d")
    closing_timestamp = factory.Faker("date_time_between", start_date="+1d", end_date="+3w")

    grace_period = sometimes_none(factory.Faker("random_int", min=1, max=10))
    contact_info = sometimes_none(factory.Faker("agency_contact_description"))

    announcement_assistance_listing = factory.SubFactory(
        AnnouncementAssistanceListingFactory, announcement=factory.SelfAttribute("..announcement")
    )

    application_package_forms = factory.RelatedFactoryList(
        "tests.db.models.factories.ApplicationPackageFormFactory",
        factory_related_name="application_package",
        size=1,
    )

    # Default to allowing both individual and organization applicants
    # This can be overridden in tests by setting it explicitly
    open_to_applicants = [
        ApplicationPackageOpenToApplicant.INDIVIDUAL,
        ApplicationPackageOpenToApplicant.ORGANIZATION,
    ]


class ApplicationPackageFormFactory(BaseFactory):
    class Meta:
        model = application_package_models.ApplicationPackageForm

    application_package_form_id = Generators.UuidObj

    application_package = factory.SubFactory(ApplicationPackageFactory)
    application_package_id = factory.LazyAttribute(
        lambda a: a.application_package.application_package_id
    )

    # We'll probably want to adjust this in the future, but for now just a random int for the form
    form_id = factory.Faker("random_int", min=100, max=150)

    is_required = factory.Faker("boolean")


###################
# Test Factories
###################


class ExampleTableFactory(BaseFactory):
    class Meta:
        model = db_test_models.ExampleTable

    example_id = Generators.UuidObj

    description = factory.Faker("paragraph", nb_sentences=1)
    my_count = factory.Faker("random_int", min=1, max=10)

    friends = factory.RelatedFactoryList(
        "tests.db.models.factories.FriendTableFactory",
        factory_related_name="example",
        size=lambda: random.randint(1, 3),
    )


class FriendTableFactory(BaseFactory):
    class Meta:
        model = db_test_models.FriendTable

    friend_id = Generators.UuidObj

    example = factory.SubFactory(ExampleTableFactory)
    example_id = factory.LazyAttribute(lambda f: f.example.example_id)

    friend_types = factory.Faker(
        "random_elements",
        length=random.randint(1, 3),
        elements=[f for f in db_test_models.FriendType],
        unique=True,
    )


###################
# Extract Factories
###################


class PendingFileFactory(BaseFactory):
    class Meta:
        model = file_upload_models.PendingFile

    pending_file_id = Generators.UuidObj

    user = factory.SubFactory(UserFactory)
    user_id = factory.LazyAttribute(lambda p: p.user.user_id)

    file_name = factory.Faker("file_name")
    file_location = factory.Faker("file_path")
    mime_type = "plain/text"
    file_scan_status = FileScanStatus.PENDING

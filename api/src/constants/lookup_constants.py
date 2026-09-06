from enum import StrEnum


class JobType(StrEnum):
    MIGRATE_UP = "migrate-up"
    MIGRATE_DOWN = "migrate-down"
    MIGRATE_DOWNALL = "migrate-downall"
    FETCH_ASSISTANCE_LISTING = "fetch-assistance-listing"


class UserType(StrEnum):
    STANDARD = "standard"
    INTERNAL_FRONTEND = "internal_frontend"


class ExternalUserType(StrEnum):
    LOGIN_GOV = "login_gov"


class Privilege(StrEnum):
    VIEW_PARTNER = "view_partner"
    UPDATE_PARTNER = "update_partner"
    MANAGE_PARTNER_MEMBERS = "manage_partner_members"

    VIEW_PROGRAM = "view_program"
    UPDATE_PROGRAM = "update_program"

    VIEW_GRANTOR_ORGANIZATION = "view_grantor_organization"
    UPDATE_GRANTOR_ORGANIZATION = "update_grantor_organization"
    MANAGE_GRANTOR_ORGANIZATION_MEMBERS = "manage_grantor_organization_members"

    INTERNAL_WORKFLOW_EVENT_SEND = "internal_workflow_event_send"

    UNUSED_PRIVILEGE_102 = "unused_privilege_102"
    UNUSED_PRIVILEGE_103 = "unused_privilege_103"


class ResourceType(StrEnum):
    INTERNAL = "internal"
    PARTNER = "partner"
    PROGRAM = "program"
    GRANTOR_ORGANIZATION = "grantor_organization"
    OPPORTUNITY = "opportunity"


class GrantorOrganizationType(StrEnum):
    PROGRAM_OFFICE = "program_office"
    GRANT_OFFICE = "grant_office"


class OpportunityCategory(StrEnum):
    DISCRETIONARY = "discretionary"
    MANDATORY = "mandatory"
    CONTINUATION = "continuation"
    EARMARK = "earmark"
    OTHER = "other"


class ApplicantType(StrEnum):
    STATE_GOVERNMENTS = "state_governments"
    COUNTY_GOVERNMENTS = "county_governments"
    CITY_OR_TOWNSHIP_GOVERNMENTS = "city_or_township_governments"
    SPECIAL_DISTRICT_GOVERNMENTS = "special_district_governments"
    INDEPENDENT_SCHOOL_DISTRICTS = "independent_school_districts"
    PUBLIC_AND_STATE_INSTITUTIONS_OF_HIGHER_EDUCATION = (
        "public_and_state_institutions_of_higher_education"
    )
    PRIVATE_INSTITUTIONS_OF_HIGHER_EDUCATION = "private_institutions_of_higher_education"
    FEDERALLY_RECOGNIZED_NATIVE_AMERICAN_TRIBAL_GOVERNMENTS = (
        "federally_recognized_native_american_tribal_governments"
    )
    OTHER_NATIVE_AMERICAN_TRIBAL_ORGANIZATIONS = (
        "other_native_american_tribal_organizations"
    )
    PUBLIC_AND_INDIAN_HOUSING_AUTHORITIES = "public_and_indian_housing_authorities"
    NONPROFITS_NON_HIGHER_EDUCATION_WITH_501C3 = (
        "nonprofits_non_higher_education_with_501c3"
    )
    NONPROFITS_NON_HIGHER_EDUCATION_WITHOUT_501C3 = (
        "nonprofits_non_higher_education_without_501c3"
    )
    INDIVIDUALS = "individuals"
    FOR_PROFIT_ORGANIZATIONS_OTHER_THAN_SMALL_BUSINESSES = (
        "for_profit_organizations_other_than_small_businesses"
    )
    SMALL_BUSINESSES = "small_businesses"
    OTHER = "other"
    UNRESTRICTED = "unrestricted"


class FundingCategory(StrEnum):
    RECOVERY_ACT = "recovery_act"
    AGRICULTURE = "agriculture"
    ARTS = "arts"
    BUSINESS_AND_COMMERCE = "business_and_commerce"
    COMMUNITY_DEVELOPMENT = "community_development"
    CONSUMER_PROTECTION = "consumer_protection"
    DISASTER_PREVENTION_AND_RELIEF = "disaster_prevention_and_relief"
    EDUCATION = "education"
    EMPLOYMENT_LABOR_AND_TRAINING = "employment_labor_and_training"
    ENERGY = "energy"
    ENVIRONMENT = "environment"
    FOOD_AND_NUTRITION = "food_and_nutrition"
    HEALTH = "health"
    HOUSING = "housing"
    HUMANITIES = "humanities"
    INFRASTRUCTURE_INVESTMENT_AND_JOBS_ACT = "infrastructure_investment_and_jobs_act"
    INFORMATION_AND_STATISTICS = "information_and_statistics"
    INCOME_SECURITY_AND_SOCIAL_SERVICES = "income_security_and_social_services"
    LAW_JUSTICE_AND_LEGAL_SERVICES = "law_justice_and_legal_services"
    NATURAL_RESOURCES = "natural_resources"
    OPPORTUNITY_ZONE_BENEFITS = "opportunity_zone_benefits"
    REGIONAL_DEVELOPMENT = "regional_development"
    SCIENCE_TECHNOLOGY_AND_OTHER_RESEARCH_AND_DEVELOPMENT = (
        "science_technology_and_other_research_and_development"
    )
    TRANSPORTATION = "transportation"
    AFFORDABLE_CARE_ACT = "affordable_care_act"
    OTHER = "other"
    ENERGY_INFRASTRUCTURE_AND_CRITICAL_MINERAL_AND_MATERIALS = (
        "energy_infrastructure_and_critical_mineral_and_materials"
    )
    RECREATION_AND_TOURISM = "recreation_and_tourism"


class FundingInstrument(StrEnum):
    COOPERATIVE_AGREEMENT = "cooperative_agreement"
    GRANT = "grant"
    PROCUREMENT_CONTRACT = "procurement_contract"
    OTHER = "other"


class CompetitionOpenToApplicant(StrEnum):
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"


class OpportunityAuditEvent(StrEnum):
    OPPORTUNITY_CREATED = "opportunity_created"
    OPPORTUNITY_UPDATED = "opportunity_updated"
    OPPORTUNITY_SUMMARY_CREATED = "opportunity_summary_created"
    OPPORTUNITY_SUMMARY_UPDATED = "opportunity_summary_updated"
    COMPETITION_CREATED = "competition_created"
    COMPETITION_UPDATED = "competition_updated"


class PartnerAuditEvent(StrEnum):
    USER_ROLES_MODIFIED = "user_roles_modified"


class GrantorOrganizationAuditEvent(StrEnum):
    USER_ROLES_MODIFIED = "user_roles_modified"


class WorkflowType(StrEnum):
    BASIC_TEST_WORKFLOW = "basic_test_workflow"
    PROTOTYPE_WORKFLOW = "prototype_workflow"
    APPROVAL_TEST_WORKFLOW = "approval_test_workflow"
    LIMITED_APPROVAL_TEST_WORKFLOW = "limited_approval_test_workflow"

    def get_human_friendly_text(self) -> str:
        return self.value.replace("_", " ").title()


class ApprovalType(StrEnum):
    BASIC_TEST_APPROVAL = "basic_test_approval"
    SECONDARY_TEST_APPROVAL = "secondary_test_approval"


class ApprovalResponseType(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"
    REQUIRES_MODIFICATION = "requires_modification"


class WorkflowEventType(StrEnum):
    START_WORKFLOW = "start_workflow"
    PROCESS_WORKFLOW = "process_workflow"


class WorkflowEventProcessingResult(StrEnum):
    """Enum representing the result of processing an SQS event."""

    SUCCESS = "success"
    NON_RETRYABLE_ERROR = "non_retryable_error"
    RETRYABLE_ERROR = "retryable_error"
    GENERAL_ERROR = "general_error"


class ResourceInheritance(StrEnum):
    """How far up the resource hierarchy a user lookup should reach.

    Not a lookup table - this is an API filter value, so it has no DB representation.
    """

    FULL = "full"
    DIRECT = "direct"


ALLOWED_RESOURCES_FOR_PRIVILEGE: dict[Privilege, set[ResourceType]] = {
    Privilege.VIEW_PARTNER: {ResourceType.PARTNER},
    Privilege.UPDATE_PARTNER: {ResourceType.PARTNER},
    Privilege.MANAGE_PARTNER_MEMBERS: {ResourceType.PARTNER},
    Privilege.VIEW_PROGRAM: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
        ResourceType.PROGRAM,
    },
    Privilege.UPDATE_PROGRAM: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
        ResourceType.PROGRAM,
    },
    Privilege.VIEW_GRANTOR_ORGANIZATION: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
    },
    Privilege.UPDATE_GRANTOR_ORGANIZATION: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
    },
    Privilege.MANAGE_GRANTOR_ORGANIZATION_MEMBERS: {
        ResourceType.PARTNER,
        ResourceType.GRANTOR_ORGANIZATION,
    },
    Privilege.INTERNAL_WORKFLOW_EVENT_SEND: {ResourceType.INTERNAL},
    Privilege.UNUSED_PRIVILEGE_102: set(),
    Privilege.UNUSED_PRIVILEGE_103: set(),
}


VIEW_PRIVILEGE_FOR_RESOURCE_TYPE: dict[ResourceType, Privilege] = {
    ResourceType.PARTNER: Privilege.VIEW_PARTNER,
    ResourceType.GRANTOR_ORGANIZATION: Privilege.VIEW_GRANTOR_ORGANIZATION,
    ResourceType.PROGRAM: Privilege.VIEW_PROGRAM,
}

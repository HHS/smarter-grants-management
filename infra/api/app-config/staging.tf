# api service for the staging environment (AWS account 530702498822).
#
# Mirrors dev's service set. The same bring-up deferrals apply (no ACM
# certificate / hosted zone, no SES domain identity, no New Relic entities yet),
# but staging keeps database deletion protection on since it is not expected to
# be torn down casually.
module "staging_config" {
  source         = "./env-config"
  project_name   = local.project_name
  app_name       = local.app_name
  default_region = module.project_config.default_region
  environment    = "staging"
  network_name   = "staging"

  domain_name            = null # set once DNS + an ACM certificate exist
  secondary_domain_names = []
  enable_https           = false

  has_database                  = local.has_database
  database_enable_http_endpoint = true
  database_engine_version       = "17.7"
  database_deletion_protection  = true
  database_newrelic_entity_guid = "" # Populate once the New Relic entity for the staging RDS cluster exists

  has_incident_management_service = local.has_incident_management_service
  enable_identity_provider        = local.enable_identity_provider
  enable_notifications            = false # Enable once an SES domain identity exists for staging

  service_newrelic_entity_guid      = "" # Populate once the New Relic entity for the staging primary ALB exists
  service_newrelic_mtls_entity_guid = "" # Populate once the New Relic entity for the staging mTLS ALB exists
  api_host_newrelic_entity_guid     = "" # Populate once the New Relic entity for the staging ECS service host exists

  instance_desired_instance_count = 2
  instance_scaling_min_capacity   = 2
  instance_scaling_max_capacity   = 4

  database_min_capacity   = 2
  database_max_capacity   = 8
  database_instance_count = 2

  has_search            = true
  search_engine_version = "OpenSearch_2.15"
  # The reserved-SSO role suffix (AWSReservedSSO_<PermissionSet>_<suffix>) is
  # generated per AWS account. null falls back to the account root principal;
  # replace with account 530702498822's own reserved-SSO admin role to grant a
  # dedicated SSO-admin principal on the OpenSearch domain and its KMS key.
  search_sso_admin_role_name = null

  service_override_extra_environment_variables = {
    ENABLE_WORKFLOW_ENDPOINTS             = 1
    ENABLE_AWARD_RECOMMENDATION_ENDPOINTS = 1
    ENABLE_GRANTOR_OPPORTUNITY_ENDPOINTS  = 1
    ENABLE_FILE_UPLOAD_ENDPOINTS          = 1

    # Email notification
    RESET_EMAILS_WITHOUT_SENDING               = "true"
    ENABLE_ORG_SAVED_OPPORTUNITY_NOTIFICATIONS = "true"

    # PDF Generation
    DOCRAPTOR_TEST_MODE      = "true"
    PDF_GENERATION_USE_MOCKS = "false"

    # Workflow
    WORKFLOW_SERVICE_INTERNAL_USER_ID = "5711f79c-2445-47c7-bbcb-c8caa293ffad"

    # Job lock — enabled while we validate it
    ENABLE_JOB_LOCK = "true"
  }

  enable_workflow_service = true

  # Enables ECS Exec access for debugging or jump access.
  # See https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-exec.html
  # Defaults to `false`. Uncomment the next line to enable.
  # enable_command_execution = true
}

# frontend service for the staging environment (AWS account 530702498822).
#
# HTTPS/custom domain is deferred for the initial bring-up until an ACM cert +
# Route53 hosted zone exist.
module "staging_config" {
  source                          = "./env-config"
  project_name                    = local.project_name
  app_name                        = local.app_name
  default_region                  = module.project_config.default_region
  environment                     = "staging"
  network_name                    = "staging"
  domain_name                     = null # set once DNS + certs exist
  enable_https                    = false
  has_database                    = local.has_database
  has_incident_management_service = local.has_incident_management_service
  enable_identity_provider        = local.enable_identity_provider
  enable_notifications            = local.enable_notifications

  instance_desired_instance_count = 2
  instance_scaling_min_capacity   = 2
  instance_scaling_max_capacity   = 10

  service_newrelic_entity_guid      = "" # Populate once the New Relic entity for the staging frontend ALB exists
  service_host_newrelic_entity_guid = "" # Populate once the New Relic browser entity for the staging frontend exists

  # Enables ECS Exec access for debugging or jump access.
  # Defaults to `false`. Uncomment the next line to enable.
  # enable_command_execution = true
}

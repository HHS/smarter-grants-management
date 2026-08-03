output "application_log_group" {
  value = module.service.application_log_group
}

output "application_log_stream_prefix" {
  value = module.service.application_log_stream_prefix
}

output "migrator_role_arn" {
  value = module.service.migrator_role_arn
}

output "service_cluster_name" {
  value = module.service.cluster_name
}

output "service_endpoint" {
  description = "The public endpoint for the service."
  value       = module.service.public_endpoint
}

output "service_name" {
  value = local.service_config.service_name
}

# Read this after the first apply and store it in
# /api/<environment>/api-gateway-default-usage-plan-id, which the service reads as
# API_GATEWAY_DEFAULT_USAGE_PLAN_ID. The plan is created by this layer, so the SSM
# parameter has to start as a placeholder.
output "api_gateway_public_usage_plan_id" {
  value = module.service.api_gateway_public_usage_plan_id
}


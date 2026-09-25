# ClamAV virus scanner for the file-scan S3 bucket.
#
# Uploads land under unscanned/ in the file-scan bucket (created by
# modules/service from the s3_buckets config). Each ObjectCreated event invokes
# the scanner Lambda, which scans the object with clamd, moves it to scanned/ or
# infected/, posts the outcome to the API, and updates the DynamoDB scan-cache
# record the upload client polls. A second Lambda runs freshclam on a schedule to
# keep the signature database on EFS current.
#
# Before the first terraform apply on a fresh checkout, build the ClamAV Lambda
# layer locally:
#
#   ./infra/modules/clamav/build-layer.sh
#
# That script uses Docker to extract clamav binaries from Amazon Linux 2023 and
# writes layer.zip next to itself. The module's first apply invokes freshclam
# synchronously to populate the signature database before S3 starts delivering
# events; until that completes the scanner logs "signature database not yet
# populated on EFS".

locals {
  # The scanner posts results back to the API at POST <api_base_url>/v1/files/<file_id>.
  # Prefer an explicit callback host, then the environment's public domain. Neither
  # exists yet in dev or staging — domain_name stays null until DNS and an ACM
  # certificate land — so fall back to the ALB's own DNS name. The scanner runs in
  # the private subnets with NAT egress, so it can reach the internet-facing ALB.
  scanner_callback_hosts = compact([
    local.service_config.scanner_callback_domain_name,
    local.service_config.domain_name,
  ])

  scanner_api_base_url = (length(local.scanner_callback_hosts) > 0
    ? "https://${local.scanner_callback_hosts[0]}"
    : module.service.public_endpoint
  )

  enable_file_scanning = module.app_config.enable_file_scanning
}

# API key the scanner authenticates with (X-API-Key) when posting scan results.
# Stored out-of-band as a SecureString, the same manual-secret convention the
# rest of the API's secrets use (see infra/api/app-config/env-config/environment_variables.tf).
# It must match the key_id on the internal scanner user's user_api_key row.
#
# Like every other manage_method = "manual" secret in this app, this is a plain
# data source: it fails at PLAN time if the parameter does not exist, which is
# why the whole module is gated on enable_file_scanning.
data "aws_ssm_parameter" "file_scan_api_key" {
  count = local.enable_file_scanning ? 1 : 0
  name  = "/api/${var.environment_name}/file-scan-api-key"
}

module "clamav" {
  count  = local.enable_file_scanning ? 1 : 0
  source = "../../modules/clamav"

  name = "${local.service_name}-clamav"

  s3_bucket_id  = module.service.s3_bucket_ids["file-scan"]
  s3_bucket_arn = module.service.s3_bucket_arns["file-scan"]

  vpc_id             = data.aws_vpc.network.id
  private_subnet_ids = data.aws_subnets.private.ids

  api_base_url      = local.scanner_api_base_url
  file_scan_api_key = data.aws_ssm_parameter.file_scan_api_key[0].value

  file_scan_cache_table_name = module.file_scan_cache.table_name
  dynamodb_write_policy_arn  = module.file_scan_cache.write_access_policy_arn

  enable_newrelic      = module.project_config.enable_newrelic
  newrelic_entity_guid = local.service_config.newrelic_host_entity_guid

  scanner_provisioned_concurrency = local.service_config.scanner_provisioned_concurrency
}

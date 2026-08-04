# =============================================================================
# NEW RELIC DISABLED
#
# This project has no New Relic tenant yet, so the AWS <-> New Relic cloud
# integration is commented out to let brand new accounts bootstrap. As written
# it would block `make infra-set-up-account` in three ways:
#
#   1. `data.aws_ssm_parameter.newrelic_account_id` fails unless the
#      /new-relic-account-id SSM parameter already exists.
#   2. The module needs the `newrelic` provider, whose empty configuration block
#      in main.tf reads NEW_RELIC_ACCOUNT_ID and NEW_RELIC_API_KEY at plan time.
#   3. The module source is fetched from GitHub at `terraform init`.
#
# To re-enable:
#   1. Uncomment the `newrelic` required_provider and the `provider "newrelic"`
#      block in main.tf.
#   2. Uncomment everything below.
#   3. Create the /new-relic-account-id SSM parameter with the real account id
#      and export NEW_RELIC_ACCOUNT_ID / NEW_RELIC_API_KEY.
#   4. Update the linked-account name below — it still says "simpler-grants-gov".
#   5. Re-run `make infra-update-current-account` per account.
#
# The log forwarders in infra/modules/{service,database,search} are disabled
# separately, via the `enable_newrelic` flag in infra/project-config/main.tf.
# =============================================================================

# Kept declared (outside the commented block) because the setup scripts pass
# TF_VAR_account_name, and because the tags/description in other account
# resources may want it later.
variable "account_name" {
  type        = string
  description = "Human-readable name of the AWS account being configured (e.g. \"dev\", \"staging\"). Passed via TF_VAR_account_name by the setup scripts; falls back to the account id if unset."
  default     = ""
}

# data "aws_ssm_parameter" "newrelic_account_id" {
#   name = "/new-relic-account-id"
# }
#
# locals {
#   # New Relic linked-account names must be unique within the New Relic account.
#   newrelic_link_name_full = (
#     local.is_admin_account
#     ? "smarter-grants-management"
#     : "smarter-grants-management-${coalesce(var.account_name, data.aws_caller_identity.current.account_id)}"
#   )
#
#   newrelic_link_name = length(local.newrelic_link_name_full) > 24 ? substr(local.newrelic_link_name_full, 0, 24) : local.newrelic_link_name_full
# }
#
# module "newrelic-aws-cloud-integrations" {
#   source = "github.com/newrelic/terraform-provider-newrelic//examples/modules/cloud-integrations/aws?ref=v3.58.1"
#
#   newrelic_account_id     = data.aws_ssm_parameter.newrelic_account_id.value
#   newrelic_account_region = "US"
#   name                    = local.newrelic_link_name
#
#   # checkov:skip=CKV_TF_1: I would rather not use a commit hash
# }

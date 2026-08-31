data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  # AWS account that acts as the Security Hub delegated administrator and the
  # central CloudTrail logging account for this project. Only this account manages
  # the CloudTrail trails and Security Hub standards subscriptions. Kept in one
  # place so the account ID isn't hardcoded across cloudtrail.tf, security_hub.tf,
  # and monitoring.tf.
  #
  # dev is the admin account for this project. It previously pointed at
  # simpler-grants-gov's delegated administrator (315341936575), which matched
  # neither of this project's accounts — so is_admin_account was false in both and
  # NEITHER got a CloudTrail trail. cloudtrail.tf now creates the central log
  # bucket and KMS key in this account rather than referencing that foreign
  # account's buckets by hardcoded name.
  admin_account_id = "135002447353" # dev
  is_admin_account = data.aws_caller_identity.current.account_id == local.admin_account_id

  # Must match tf_state_bucket_name in bin/set-up-current-account, which creates
  #
  # The terraform-backend-s3 module appends "-logs" for the access-log bucket,
  tf_state_bucket_name = lookup(
    module.project_config.tf_state_bucket_name_overrides,
    data.aws_caller_identity.current.account_id,
    "${module.project_config.project_name}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.name}-tf-state"
  )

  # Choose the region where this infrastructure should be deployed.
  region = module.project_config.default_region

  # Set project tags that will be used to tag all resources.
  tags = merge(module.project_config.default_tags, {
    description = "Backend resources required for terraform state management and GitHub authentication with AWS."
  })
}

terraform {

  required_version = "1.14.3"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.68.0"
    }
    # Used by security_hub_alerts.tf to build the alerting Lambda packages from
    # their committed .py sources.
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    # NEW RELIC DISABLED — see monitoring.tf.
    # An empty `provider "newrelic" {}` block reads NEW_RELIC_ACCOUNT_ID and
    # NEW_RELIC_API_KEY at plan time and fails without them, which would block
    # bootstrapping an account that has no New Relic tenant yet. Re-enable this
    # together with the module in monitoring.tf.
    # newrelic = {
    #   source  = "newrelic/newrelic"
    #   version = "~> 3.57"
    # }
  }

  backend "s3" {
    encrypt = "true"
  }
}

# NEW RELIC DISABLED — see monitoring.tf
# provider "newrelic" {}

provider "aws" {
  region = local.region
  default_tags {
    tags = local.tags
  }
}

module "project_config" {
  source = "../project-config"
}

module "backend" {
  source = "../modules/terraform-backend-s3"
  name   = local.tf_state_bucket_name
}

module "auth_github_actions" {
  source                   = "../modules/auth-github-actions"
  github_actions_role_name = module.project_config.github_actions_role_name
  # The OIDC subject claim, NOT the human-readable "org/repo". This org issues
  # ID-based subjects ("<owner>@<owner_id>/<repo>@<repo_id>"), which is what the
  # trust policy has to match.
  github_repository = module.project_config.github_oidc_subject_repository
  allowed_actions   = [for aws_service in module.project_config.aws_services : "${aws_service}:*"]
}

data "aws_iam_role" "github_actions" {
  name = module.project_config.github_actions_role_name
}

locals {
  # Set project tags that will be used to tag all resources.
  tags = merge(module.project_config.default_tags, {
    application      = module.app_config.app_name
    application_role = "build-repository"
    environment      = var.environment_name
    description      = "Backend resources required for storing built release candidate artifacts to be used for deploying to environments."
  })

  build_repository_config = module.app_config.build_repository_config

  network_config = module.project_config.network_configs[var.environment_name]

}

terraform {
  required_version = "1.14.3"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.68.0"
    }
  }

  backend "s3" {
    encrypt = "true"
  }
}

provider "aws" {
  region = local.build_repository_config.region
  # Refuse to operate against the wrong account (covers plan/apply/destroy).
  allowed_account_ids = [module.expected_account.account_id]
  default_tags {
    tags = local.tags
  }
}

module "project_config" {
  source = "../../project-config"
}

module "app_config" {
  source = "../app-config"
}


module "expected_account" {
  source       = "../../modules/account-id-by-name"
  account_name = local.network_config.account_name
  accounts_dir = "${path.module}/../../accounts"
}

module "account_guard" {
  source              = "../../modules/aws-account-guard"
  expected_account_id = module.expected_account.account_id
  context             = "the ${var.environment_name} frontend build repository"
}

module "container_image_repository" {
  source               = "../../modules/container-image-repository"
  name                 = local.build_repository_config.name
  push_access_role_arn = data.aws_iam_role.github_actions.arn
}

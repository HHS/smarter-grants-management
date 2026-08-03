locals {
  image_repository_name   = "${local.project_name}-${local.app_name}"
  image_repository_region = module.project_config.default_region

  # Only the repository name and region are shared across environments. The AWS
  # account is deliberately absent: each environment owns a build repository in its
  # own account, so the account — and therefore the repository ARN and URL — is
  # resolved per environment by the layer that needs it. See
  # image_repository_account_id in infra/api/service/main.tf.
  build_repository_config = {
    name   = local.image_repository_name
    region = local.image_repository_region
  }
}

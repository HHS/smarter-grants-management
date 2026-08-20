locals {
  image_repository_name   = "${local.project_name}-${local.app_name}"
  image_repository_region = module.project_config.default_region

  build_repository_config = {
    name   = local.image_repository_name
    region = local.image_repository_region
  }
}

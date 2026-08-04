output "aws_services" {
  description = "AWS services that this project uses"
  value       = local.aws_services
}

output "code_repository" {
  value       = regex("([-_\\w]+/[-_\\w]+)(\\.git)?$", local.code_repository_url)[0]
  description = "The 'org/repo' string of the repo (e.g. 'navapbc/template-infra'). This is extracted from the repo URL (e.g. 'git@github.com:navapbc/template-infra.git' or 'https://github.com/navapbc/template-infra.git')"
}

output "code_repository_url" {
  value = local.code_repository_url
}

output "github_oidc_subject_repository" {
  value       = local.github_oidc_subject_repository
  description = "Repository portion of the GitHub OIDC 'sub' claim, in GitHub's ID-based format '<owner>@<owner_id>/<repo>@<repo_id>'. Used to build the GitHub Actions role trust policy. Distinct from code_repository, which is the human-readable 'org/repo' used for URLs."
}

output "default_region" {
  value = local.default_region
}

output "enable_newrelic" {
  value       = local.enable_newrelic
  description = "Whether to create the New Relic log forwarders. False while this project has no New Relic tenant."
}

output "enable_security_hub_alerts" {
  value       = local.enable_security_hub_alerts
  description = "Whether to create the Security Hub alerting stack. False until the grants-alerts-email secret exists in each account."
}

output "enable_security_hub_slack" {
  value       = local.enable_security_hub_slack
  description = "Whether to post Security Hub findings to Slack. Requires enable_security_hub_alerts and the security-hub-slack-webhook secret."
}

output "enable_security_hub_standards" {
  value       = local.enable_security_hub_standards
  description = "Whether to manage Security Hub standards subscriptions locally. False while these accounts are governed by an organization-level central configuration policy."
}

output "default_tags" {
  value = {
    project             = local.project_name
    owner               = local.owner
    repository          = local.code_repository_url
    terraform           = true
    terraform_workspace = terraform.workspace
    # description is set in each environments local use key project_description if required.
  }
}

output "github_actions_role_name" {
  value = local.github_actions_role_name
}

output "network_configs" {
  value = local.network_configs
}

output "owner" {
  value = local.owner
}

output "project_name" {
  value = local.project_name
}

output "aws_services_security_group_name_prefix" {
  value = local.aws_services_security_group_name_prefix
}

output "system_notifications_config" {
  value = local.system_notifications_config
}

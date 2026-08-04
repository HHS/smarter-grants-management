locals {
  # Machine readable project name (lower case letters, dashes, and underscores)
  # This will be used in names of AWS resources, including the terraform state
  # bucket that infra/accounts/main.tf derives as
  # "${project_name}-${account_id}-${region}-tf-state".
  project_name = "smarter-grants-management"

  # Project owner (e.g. navapbc). Used for tagging infra resources.
  owner = "navapbc"

  # URL of project source code repository
  code_repository_url = "https://github.com/HHS/smarter-grants-management"

  # The repository portion of the GitHub OIDC `sub` claim, used to build the
  # trust policy for the GitHub Actions IAM role.
  #
  # This org uses GitHub's ID-based (rename-proof) subject format,
  # "<owner>@<owner_id>/<repo>@<repo_id>", rather than the plain "<owner>/<repo>"
  # form. It is kept separate from code_repository (derived from
  # code_repository_url above) because:
  #   1. code_repository is also used to build https://github.com/<repo> links,
  #      which must stay human-readable, and
  #   2. the regex that derives it uses [-_\w]+, which does not match "@".
  #
  # Verify the exact value against a real token by running the
  # check-ci-cd-auth.yml workflow, or by inspecting a failed AssumeRole event in
  # CloudTrail — the rejected `sub` is recorded there.
  github_oidc_subject_repository = "HHS@1470878/smarter-grants-management@1315368029"

  # Default AWS region for project (e.g. us-east-1, us-east-2, us-west-1).
  # This is dependent on where your project is located (if regional)
  # otherwise us-east-1 is a good default

  default_region = "us-east-1"

  github_actions_role_name                = "${local.project_name}-github-actions"
  aws_services_security_group_name_prefix = "aws-service-vpc-endpoints"

  # Whether to ship logs to New Relic.
  #
  # Disabled: this project has no New Relic tenant yet. When false, the log
  # forwarder Lambdas (and the CloudWatch subscription filters, IAM roles, and
  # Firehose plumbing around them) in infra/modules/{service,database,search}
  # are not created, and the /new-relic-license-key SSM parameter they read is
  # not required — which is what would otherwise fail every apply.
  #
  # To enable: create the /new-relic-license-key SSM parameter in the target
  # account, flip this to true, and re-apply the network/service/database layers.
  # The account-level AWS <-> New Relic integration is separate and is commented
  # out in infra/accounts/monitoring.tf.
  enable_newrelic = false

  # Whether to create the Security Hub SNS/Lambda alerting stack in
  # infra/accounts/security_hub_alerts.tf (findings topic, EventBridge rules,
  # email-formatter Lambda, and the log-failure email subscription in alarms.tf).
  #
  # Disabled: every one of those resources needs a Secrets Manager secret named
  # `grants-alerts-email` to already exist in the target account, resolved through
  # a data source that fails at PLAN time when it is missing. Leaving this on
  # would block bootstrapping either account from a clean checkout.
  #
  # To enable, in each account:
  #   aws secretsmanager create-secret --name grants-alerts-email \
  #     --secret-string '{"email":"grants-alerts@navapbc.com"}' --region us-east-1
  # then flip this to true and re-apply the accounts layer.
  enable_security_hub_alerts = false

  # Whether to additionally post Security Hub findings to Slack. Requires
  # enable_security_hub_alerts (the Slack Lambda subscribes to the findings topic
  # that flag creates) plus a `security-hub-slack-webhook` secret:
  #   aws secretsmanager create-secret --name security-hub-slack-webhook \
  #     --secret-string '{"webhook_url":"https://hooks.slack.com/services/..."}' \
  #     --region us-east-1
  enable_security_hub_slack = false
}

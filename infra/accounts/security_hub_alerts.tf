#===================================
# Security Hub Alerts
#===================================
#
# This whole stack is opt-in, gated on project_config.enable_security_hub_alerts
# (and enable_security_hub_slack for the Slack path). Both the email and Slack
# paths read a Secrets Manager secret through a data source, which fails at PLAN
# time when the secret is absent — so leaving these ungated made the accounts
# layer un-appliable from a clean checkout in an account where the secrets had not
# been hand-created. See infra/project-config/main.tf for how to turn them on.

locals {
  alerts_count = module.project_config.enable_security_hub_alerts ? 1 : 0

  # The Slack path subscribes to the findings topic that the alerts flag creates,
  # so it needs both flags on.
  slack_count = module.project_config.enable_security_hub_alerts && module.project_config.enable_security_hub_slack ? 1 : 0
}

# SNS Topic for Security Hub findings
# trivy:ignore:AVD-AWS-0095
resource "aws_sns_topic" "security_hub_findings" {
  count = local.alerts_count

  name = "security-hub-findings"
  # checkov:skip=CKV_AWS_26:SNS encryption for alerts is unnecessary
}

#===================================
# Alerts Email Configuration
#===================================

# Store alerts email in Secrets Manager to avoid exposing in terraform
# To set or update the email:
# aws secretsmanager create-secret --name grants-alerts-email \
#   --secret-string '{"email":"grants-alerts@navapbc.com"}' --region us-east-1
# Or to update:
# aws secretsmanager put-secret-value --secret-id grants-alerts-email \
#   --secret-string '{"email":"grants-alerts@navapbc.com"}' --region us-east-1

data "aws_secretsmanager_secret" "alerts_email" {
  count = local.alerts_count

  name = "grants-alerts-email"
}

data "aws_secretsmanager_secret_version" "alerts_email" {
  count = local.alerts_count

  secret_id = data.aws_secretsmanager_secret.alerts_email[0].id
}

locals {
  # Read through a splat so this stays total when the stack is disabled: a bare
  # [0] would still be evaluated and fail with an index error.
  alerts_email_secret_string = one(data.aws_secretsmanager_secret_version.alerts_email[*].secret_string)
  alerts_email               = local.alerts_email_secret_string != null ? jsondecode(local.alerts_email_secret_string)["email"] : null
}

#===================================
# Formatted Email Alerts
#===================================

# Separate SNS topic for formatted email alerts
# trivy:ignore:AVD-AWS-0095
resource "aws_sns_topic" "security_hub_findings_formatted" {
  count = local.alerts_count

  name = "security-hub-findings-formatted"
  # checkov:skip=CKV_AWS_26:SNS encryption for alerts is unnecessary
}

# Email subscription for formatted findings
resource "aws_sns_topic_subscription" "security_hub_findings_email" {
  count = local.alerts_count

  topic_arn = aws_sns_topic.security_hub_findings_formatted[0].arn
  protocol  = "email"
  endpoint  = local.alerts_email
}

# Build the deployment package from the committed .py source rather than expecting
# a pre-built .zip: infra/.gitignore excludes **/lambda/*.zip, so a checked-out
# copy of this repo has only the source. Same pattern as
# infra/modules/database/log_forwarding.tf and infra/modules/search/role_mappings.tf.
data "archive_file" "format_security_hub_email" {
  type        = "zip"
  output_path = "${path.module}/lambda/format_security_hub_email.zip"

  source {
    filename = "format_security_hub_email.py"
    content  = file("${path.module}/lambda/format_security_hub_email.py")
  }
}

# Lambda function to format findings for email
resource "aws_lambda_function" "format_security_hub_email" {
  count = local.alerts_count

  # checkov:skip=CKV_AWS_117:VPC not required for simple alerting lambda that only publishes to SNS
  # checkov:skip=CKV_AWS_116:DLQ not needed - failed alerts are not critical enough to require retry
  # checkov:skip=CKV_AWS_115:Concurrent execution limit not needed for low-volume alerting
  # checkov:skip=CKV_AWS_272:Code signing not required for internal alerting lambda
  # checkov:skip=CKV_AWS_173:Environment variables contain only SNS ARN, not sensitive data
  # checkov:skip=CKV_AWS_50:X-Ray tracing not needed for simple alerting lambda
  filename         = data.archive_file.format_security_hub_email.output_path
  function_name    = "security-hub-email-formatter"
  role             = aws_iam_role.security_hub_email_formatter[0].arn
  handler          = "format_security_hub_email.handler"
  source_code_hash = data.archive_file.format_security_hub_email.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30

  environment {
    variables = {
      EMAIL_SNS_TOPIC_ARN = aws_sns_topic.security_hub_findings_formatted[0].arn
    }
  }
}

# IAM role for email formatter Lambda
resource "aws_iam_role" "security_hub_email_formatter" {
  count = local.alerts_count

  name = "security-hub-email-formatter-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "formatter_lambda_basic" {
  count = local.alerts_count

  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.security_hub_email_formatter[0].name
}

resource "aws_iam_role_policy" "formatter_sns_publish" {
  count = local.alerts_count

  name = "sns-publish"
  role = aws_iam_role.security_hub_email_formatter[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sns:Publish"
        ]
        Effect   = "Allow"
        Resource = aws_sns_topic.security_hub_findings_formatted[0].arn
      }
    ]
  })
}

resource "aws_lambda_permission" "allow_sns_formatter" {
  count = local.alerts_count

  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.format_security_hub_email[0].function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.security_hub_findings[0].arn
}

# SNS subscription to trigger formatter Lambda
resource "aws_sns_topic_subscription" "security_hub_findings_formatter" {
  count = local.alerts_count

  topic_arn = aws_sns_topic.security_hub_findings[0].arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.format_security_hub_email[0].arn
}

#===================================
# Slack Integration (Optional)
#===================================

# Gated on project_config.enable_security_hub_slack. To enable Slack notifications:
# 1. Create a Slack webhook URL in your Slack workspace
# 2. Store it in AWS Secrets Manager with the name below
# 3. Set enable_security_hub_slack = true in infra/project-config/main.tf
#
# aws secretsmanager create-secret \
#   --name security-hub-slack-webhook \
#   --secret-string '{"webhook_url":"https://hooks.slack.com/services/YOUR/WEBHOOK/URL"}' \
#   --region us-east-1

# Only the secret's arn and name are needed here — the Lambda fetches the value at
# runtime with the SDK, so there is deliberately no secret_version data source.
data "aws_secretsmanager_secret" "slack_webhook" {
  count = local.slack_count

  name = "security-hub-slack-webhook"
}

# IAM role for Lambda function
resource "aws_iam_role" "security_hub_slack_lambda" {
  count = local.slack_count

  name = "security-hub-slack-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  count = local.slack_count

  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.security_hub_slack_lambda[0].name
}

resource "aws_iam_role_policy" "lambda_secrets" {
  count = local.slack_count

  name = "secrets-access"
  role = aws_iam_role.security_hub_slack_lambda[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Effect   = "Allow"
        Resource = data.aws_secretsmanager_secret.slack_webhook[0].arn
      }
    ]
  })
}

# See the note on the email formatter's archive_file above for why the package is
# built here instead of being committed.
data "archive_file" "security_hub_slack" {
  type        = "zip"
  output_path = "${path.module}/lambda/security_hub_slack.zip"

  source {
    filename = "security_hub_slack.py"
    content  = file("${path.module}/lambda/security_hub_slack.py")
  }
}

# Lambda function to post to Slack
resource "aws_lambda_function" "security_hub_slack" {
  count = local.slack_count

  # checkov:skip=CKV_AWS_117:VPC not required for simple alerting lambda that only posts to Slack
  # checkov:skip=CKV_AWS_116:DLQ not needed - failed alerts are not critical enough to require retry
  # checkov:skip=CKV_AWS_115:Concurrent execution limit not needed for low-volume alerting
  # checkov:skip=CKV_AWS_272:Code signing not required for internal alerting lambda
  # checkov:skip=CKV_AWS_173:Environment variables contain only secret name reference, not the secret itself
  # checkov:skip=CKV_AWS_50:X-Ray tracing not needed for simple alerting lambda
  filename         = data.archive_file.security_hub_slack.output_path
  function_name    = "security-hub-slack-notifier"
  role             = aws_iam_role.security_hub_slack_lambda[0].arn
  handler          = "security_hub_slack.handler"
  source_code_hash = data.archive_file.security_hub_slack.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30

  environment {
    variables = {
      SLACK_WEBHOOK_SECRET_NAME = data.aws_secretsmanager_secret.slack_webhook[0].name
    }
  }
}

resource "aws_lambda_permission" "allow_sns" {
  count = local.slack_count

  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.security_hub_slack[0].function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.security_hub_findings[0].arn
}

# SNS subscription to trigger Lambda
resource "aws_sns_topic_subscription" "security_hub_findings_slack" {
  count = local.slack_count

  topic_arn = aws_sns_topic.security_hub_findings[0].arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.security_hub_slack[0].arn
}

# EventBridge rule for CRITICAL severity findings
# Excludes Inspector findings (CVE vulnerabilities) which are too noisy for real-time alerts
resource "aws_cloudwatch_event_rule" "security_hub_critical_findings" {
  count = local.alerts_count

  name        = "security-hub-critical-findings"
  description = "Capture CRITICAL severity findings from Security Hub (excluding Inspector)"

  event_pattern = jsonencode({
    source      = ["aws.securityhub"]
    detail-type = ["Security Hub Findings - Imported"]
    detail = {
      findings = {
        Severity = {
          Label = ["CRITICAL"]
        }
        Workflow = {
          Status = ["NEW"]
        }
        RecordState = ["ACTIVE"]
        ProductArn = [{
          "anything-but" = {
            "prefix" = "arn:aws:securityhub:us-east-1::product/aws/inspector"
          }
        }]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "security_hub_critical_findings_sns" {
  count = local.alerts_count

  rule      = aws_cloudwatch_event_rule.security_hub_critical_findings[0].name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.security_hub_findings[0].arn
}

# EventBridge rule for HIGH severity findings
# Excludes Inspector findings (CVE vulnerabilities) which are too noisy for real-time alerts
resource "aws_cloudwatch_event_rule" "security_hub_high_findings" {
  count = local.alerts_count

  name        = "security-hub-high-findings"
  description = "Capture HIGH severity findings from Security Hub (excluding Inspector)"

  event_pattern = jsonencode({
    source      = ["aws.securityhub"]
    detail-type = ["Security Hub Findings - Imported"]
    detail = {
      findings = {
        Severity = {
          Label = ["HIGH"]
        }
        Workflow = {
          Status = ["NEW"]
        }
        RecordState = ["ACTIVE"]
        ProductArn = [{
          "anything-but" = {
            "prefix" = "arn:aws:securityhub:us-east-1::product/aws/inspector"
          }
        }]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "security_hub_high_findings_sns" {
  count = local.alerts_count

  rule      = aws_cloudwatch_event_rule.security_hub_high_findings[0].name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.security_hub_findings[0].arn
}

# SNS topic policy to allow EventBridge to publish
resource "aws_sns_topic_policy" "security_hub_findings" {
  count = local.alerts_count

  arn = aws_sns_topic.security_hub_findings[0].arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEventBridgePublish"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "SNS:Publish"
        Resource = aws_sns_topic.security_hub_findings[0].arn
      }
    ]
  })
}

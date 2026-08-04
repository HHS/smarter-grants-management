# Alarm if logs aren't being created for the containers
resource "aws_cloudwatch_metric_alarm" "container_log_failure" {
  alarm_name          = "logs-missing"
  alarm_description   = "Logs failing for containers"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 5
  metric_name         = "DeliveryErrors"
  namespace           = "AWS/Logs"
  period              = 60
  statistic           = "Sum"
  treat_missing_data  = "ignore"
  alarm_actions       = [aws_sns_topic.log_failure.arn]
}
# trivy:ignore:AVD-AWS-0095
resource "aws_sns_topic" "log_failure" {
  name = "security-no-logs"
  # checkov:skip=CKV_AWS_26:SNS encryption for alerts is unnecessary
}

# Gated on the same flag as the rest of the alerting stack: local.alerts_email
# resolves from the grants-alerts-email secret, which is null until
# project_config.enable_security_hub_alerts is on. The alarm and topic above stay
# unconditional so the alarm still fires and can be subscribed to by hand.
resource "aws_sns_topic_subscription" "log_failure" {
  count = local.alerts_count

  topic_arn = aws_sns_topic.log_failure.arn
  protocol  = "email"
  endpoint  = local.alerts_email
}

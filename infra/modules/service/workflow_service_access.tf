#--------------------------------
# Workflow Service Access
#--------------------------------

# Baseline policy attachments for the workflow service task role
# (aws_iam_role.workflow_service). These are the permissions the workflow container
# needs to run at all — runtime logging, database access, and email sending — so they
# are gated on var.enable_workflow_service rather than on any OpenSearch input.
# OpenSearch-specific grants for this role live in opensearch_access.tf.

resource "aws_iam_role_policy_attachment" "workflow_service_runtime_logs" {
  count = var.enable_workflow_service ? 1 : 0

  role       = aws_iam_role.workflow_service[0].name
  policy_arn = aws_iam_policy.runtime_logs.arn
}

resource "aws_iam_role_policy_attachment" "workflow_service_db_access" {
  count = var.enable_workflow_service && var.db_vars != null ? 1 : 0

  role       = aws_iam_role.workflow_service[0].name
  policy_arn = var.db_vars.app_access_policy_arn
}

resource "aws_iam_role_policy_attachment" "workflow_service_email_access" {
  count = var.enable_workflow_service && length(var.pinpoint_app_id) > 0 ? 1 : 0

  role       = aws_iam_role.workflow_service[0].name
  policy_arn = aws_iam_policy.email_access[0].arn
}

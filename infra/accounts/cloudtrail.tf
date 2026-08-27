#===================================
# CloudTrail
#===================================

# CloudTrail per-account logging architecture
#
# Every account owns its own trails, writing to the S3 log bucket and KMS key
# created in this file. Both are scoped to the current account
# (data.aws_caller_identity.current.account_id), so each account gets a
# self-contained set: bucket, key, trails, and CloudWatch log groups.
#
# This matches how the rest of this project is laid out — each environment is
# self-contained in its own AWS account (see account_names_by_environment in
# infra/api/app-config/main.tf) — and it means a new account gets an audit trail
# from its first apply with no dependency on the AWS Organizations topology.
#
# The alternative considered was a single organization trail in the delegated
# administrator account (is_organization_trail = true), which would centralize
# logs so member accounts could not tamper with them and would avoid per-account
# cost. It was not chosen because it requires this account to be the AWS
# Organizations management account or a registered CloudTrail delegated
# administrator, with all member accounts in that org — none of which is
# established for this project. Revisit if that changes: the tradeoff here is
# that each account can modify its own logs.
#
# These are single-account multi-region trails; is_organization_trail is not set,
# so each trail captures only its own account's events. That is the intent.
locals {
  create_cloudtrail = true

  # Bucket names are globally unique, so scope by account. 54 of the 63 characters
  # S3 allows, leaving room for the "-logs" suffix on the access-log bucket.
  cloudtrail_bucket_name = "${module.project_config.project_name}-${data.aws_caller_identity.current.account_id}-cloudtrail-logs"
}

#===================================
# Central CloudTrail log bucket + KMS key
#===================================

# CloudTrail requires a KMS key whose policy lets the service encrypt log files and
# lets this account's principals read them back.
resource "aws_kms_key" "cloudtrail" {
  count = local.create_cloudtrail ? 1 : 0

  description             = "Encrypts CloudTrail log files for ${module.project_config.project_name}"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableAccountKeyAdministration"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowCloudTrailEncrypt"
        Effect    = "Allow"
        Principal = { Service = "cloudtrail.amazonaws.com" }
        Action    = "kms:GenerateDataKey*"
        Resource  = "*"
        Condition = {
          StringLike = {
            "kms:EncryptionContext:aws:cloudtrail:arn" = "arn:aws:cloudtrail:*:${data.aws_caller_identity.current.account_id}:trail/*"
          }
        }
      },
      {
        Sid       = "AllowCloudTrailDescribeKey"
        Effect    = "Allow"
        Principal = { Service = "cloudtrail.amazonaws.com" }
        Action    = "kms:DescribeKey"
        Resource  = "*"
      },
    ]
  })

  # checkov:skip=CKV2_AWS_64:Key policy is defined inline above
}

resource "aws_kms_alias" "cloudtrail" {
  count = local.create_cloudtrail ? 1 : 0

  name          = "alias/${module.project_config.project_name}-cloudtrail"
  target_key_id = aws_kms_key.cloudtrail[0].key_id
}

resource "aws_s3_bucket" "cloudtrail" {
  count = local.create_cloudtrail ? 1 : 0

  bucket = local.cloudtrail_bucket_name

  # checkov:skip=CKV_AWS_144:Cross region replication not required for audit logs
  # checkov:skip=CKV2_AWS_62:S3 bucket does not need notifications enabled
  # checkov:skip=CKV_AWS_18:Access logging on an audit-log bucket would recurse
  # checkov:skip=CKV2_AWS_61:Lifecycle configuration is defined below
}

resource "aws_s3_bucket_versioning" "cloudtrail" {
  count = local.create_cloudtrail ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail" {
  count = local.create_cloudtrail ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.cloudtrail[0].arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "cloudtrail" {
  count = local.create_cloudtrail ? 1 : 0

  bucket                  = aws_s3_bucket.cloudtrail[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "cloudtrail" {
  count = local.create_cloudtrail ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id
  rule {
    # Matches the convention used for this project's other own-account buckets in
    # modules/terraform-backend-s3. This coexists with the s3:x-amz-acl condition on
    # the bucket policy below: BucketOwnerEnforced rejects PutObject requests
    # carrying any ACL EXCEPT bucket-owner-full-control, which is the one CloudTrail
    # sends. Don't "fix" one without the other.
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "cloudtrail" {
  count = local.create_cloudtrail ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    filter {}

    # Matches the 365-day CloudWatch log group retention below.
    expiration {
      days = 365
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

data "aws_iam_policy_document" "cloudtrail_bucket" {
  count = local.create_cloudtrail ? 1 : 0

  statement {
    sid       = "AWSCloudTrailAclCheck"
    effect    = "Allow"
    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.cloudtrail[0].arn]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
  }

  statement {
    sid       = "AWSCloudTrailWrite"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.cloudtrail[0].arn}/AWSLogs/${data.aws_caller_identity.current.account_id}/*"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }

  statement {
    sid       = "DenyInsecureTransport"
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.cloudtrail[0].arn, "${aws_s3_bucket.cloudtrail[0].arn}/*"]
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "cloudtrail" {
  count = local.create_cloudtrail ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id
  policy = data.aws_iam_policy_document.cloudtrail_bucket[0].json
}

# CloudTrail.5: CloudTrail trails should be integrated with CloudWatch Logs
#
# These are gated alongside the trails themselves. They were previously
# unconditional, which left two empty log groups and an unused IAM role in every
# non-admin account.

# CloudWatch Log Group for management events trail
resource "aws_cloudwatch_log_group" "cloudtrail_management" {
  count = local.create_cloudtrail ? 1 : 0

  #checkov:skip=CKV_AWS_158:KMS encryption to be added in future update
  name              = "/aws/cloudtrail/management-events"
  retention_in_days = 365
}

# CloudWatch Log Group for pinpoint events trail
resource "aws_cloudwatch_log_group" "cloudtrail_pinpoint" {
  count = local.create_cloudtrail ? 1 : 0

  #checkov:skip=CKV_AWS_158:KMS encryption to be added in future update
  name              = "/aws/cloudtrail/pinpoint-events"
  retention_in_days = 365
}

# IAM role for CloudTrail to write to CloudWatch Logs
resource "aws_iam_role" "cloudtrail_cloudwatch" {
  count = local.create_cloudtrail ? 1 : 0

  name = "cloudtrail-cloudwatch-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# IAM policy for CloudTrail to write to CloudWatch Logs
resource "aws_iam_role_policy" "cloudtrail_cloudwatch" {
  count = local.create_cloudtrail ? 1 : 0

  name = "cloudtrail-cloudwatch-logs-policy"
  role = aws_iam_role.cloudtrail_cloudwatch[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailCreateLogStream"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.cloudtrail_management[0].arn}:*",
          "${aws_cloudwatch_log_group.cloudtrail_pinpoint[0].arn}:*"
        ]
      },
      {
        Sid    = "AWSCloudTrailPutLogEvents"
        Effect = "Allow"
        Action = [
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.cloudtrail_management[0].arn}:*",
          "${aws_cloudwatch_log_group.cloudtrail_pinpoint[0].arn}:*"
        ]
      }
    ]
  })
}

# Management events trail
resource "aws_cloudtrail" "management_events" {
  count = local.create_cloudtrail ? 1 : 0
  #checkov:skip=CKV_AWS_252:SNS topic not currently configured; findings are routed via Security Hub instead
  name                          = "management-events"
  s3_bucket_name                = aws_s3_bucket.cloudtrail[0].id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.cloudtrail[0].arn

  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.cloudtrail_management[0].arn}:*"
  cloud_watch_logs_role_arn  = aws_iam_role.cloudtrail_cloudwatch[0].arn

  depends_on = [aws_s3_bucket_policy.cloudtrail]

  advanced_event_selector {
    name = "Management events selector"
    field_selector {
      field  = "eventCategory"
      equals = ["Management"]
    }
  }
}

# Pinpoint / SES data-events trail. Captures nothing until the notifications
# feature is enabled (enable_notifications is false in both environments), but the
# trail is cheap and means the data events are recorded from the moment it is.
resource "aws_cloudtrail" "pinpoint_events" {
  count = local.create_cloudtrail ? 1 : 0
  #checkov:skip=CKV_AWS_252:SNS topic not currently configured; findings are routed via Security Hub instead
  name                          = "pinpoint-events"
  s3_bucket_name                = aws_s3_bucket.cloudtrail[0].id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.cloudtrail[0].arn

  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.cloudtrail_pinpoint[0].arn}:*"
  cloud_watch_logs_role_arn  = aws_iam_role.cloudtrail_cloudwatch[0].arn

  depends_on = [aws_s3_bucket_policy.cloudtrail]

  advanced_event_selector {
    field_selector {
      field  = "resources.type"
      equals = ["AWS::Pinpoint::App"]
    }
    field_selector {
      field  = "eventCategory"
      equals = ["Data"]
    }
  }

  advanced_event_selector {
    field_selector {
      field  = "resources.type"
      equals = ["AWS::SES::EmailIdentity"]
    }
    field_selector {
      field  = "eventCategory"
      equals = ["Data"]
    }
  }

  advanced_event_selector {
    field_selector {
      field  = "resources.type"
      equals = ["AWS::SES::ConfigurationSet"]
    }
    field_selector {
      field  = "eventCategory"
      equals = ["Data"]
    }
  }
}

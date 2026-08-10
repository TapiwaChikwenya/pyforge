# ---------------------------------------------------------------------------
# The instance gets a role, never access keys. Two capabilities:
#   1. Session Manager, so you can get a shell without opening port 22.
#   2. Reading its own secrets from SSM Parameter Store at boot.
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "assume_ec2" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "instance" {
  name               = "${local.name}-instance"
  assume_role_policy = data.aws_iam_policy_document.assume_ec2.json
}

# Managed policy that enables Session Manager (shell without SSH).
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Read only this deployment's parameters — not every secret in the account.
data "aws_iam_policy_document" "read_secrets" {
  statement {
    sid    = "ReadOwnParameters"
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
    ]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}/*",
    ]
  }

  statement {
    sid       = "DecryptWithDefaultSsmKey"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${data.aws_region.current.name}.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "read_secrets" {
  name   = "${local.name}-read-secrets"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.read_secrets.json
}

# Optional: upload daily Postgres dumps to S3 when backup_s3_bucket is set.
data "aws_iam_policy_document" "backup_s3" {
  count = var.backup_s3_bucket != "" ? 1 : 0

  statement {
    sid    = "PutOwnBackups"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:AbortMultipartUpload",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::${var.backup_s3_bucket}",
      "arn:aws:s3:::${var.backup_s3_bucket}/*",
    ]
  }
}

resource "aws_iam_role_policy" "backup_s3" {
  count  = var.backup_s3_bucket != "" ? 1 : 0
  name   = "${local.name}-backup-s3"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.backup_s3[0].json
}

resource "aws_iam_instance_profile" "instance" {
  name = "${local.name}-instance"
  role = aws_iam_role.instance.name
}

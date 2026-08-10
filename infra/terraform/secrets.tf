# ---------------------------------------------------------------------------
# Secrets live in SSM Parameter Store (SecureString, free tier). The instance
# reads them at boot with its role — they are never baked into the image, the
# AMI, or user_data.
#
# SECRET_KEY and the database password are generated here so you never have to
# invent them. The GitHub OAuth values come from you.
# ---------------------------------------------------------------------------

resource "random_password" "session_key" {
  length  = 48
  special = false # signing key: alphanumeric keeps it shell- and env-safe
}

resource "random_password" "postgres" {
  length  = 32
  special = false # IMPORTANT: no @ / : characters, which would break the
  # postgresql://user:pass@host/db connection string
}

resource "aws_ssm_parameter" "session_key" {
  name        = "${local.ssm_prefix}/SECRET_KEY"
  description = "PyForge session cookie signing key"
  type        = "SecureString"
  value       = random_password.session_key.result

  lifecycle {
    # Rotating this signs everyone out; do it deliberately, not on every apply.
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "postgres_password" {
  name        = "${local.ssm_prefix}/POSTGRES_PASSWORD"
  description = "PyForge Postgres password"
  type        = "SecureString"
  value       = random_password.postgres.result

  lifecycle {
    # Changing this after the database volume exists would lock the app out.
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "github_client_id" {
  name        = "${local.ssm_prefix}/GITHUB_CLIENT_ID"
  description = "GitHub OAuth client id (empty disables sign-in)"
  type        = "SecureString"
  value       = var.github_client_id == "" ? "unset" : var.github_client_id
}

resource "aws_ssm_parameter" "github_client_secret" {
  name        = "${local.ssm_prefix}/GITHUB_CLIENT_SECRET"
  description = "GitHub OAuth client secret (empty disables sign-in)"
  type        = "SecureString"
  value       = var.github_client_secret == "" ? "unset" : var.github_client_secret
}

# ---------------------------------------------------------------------------
# Non-secret application settings live in the same place, so the instance can
# build its entire .env.hosted from one SSM call.
#
# Why this matters: none of these values pass through user_data, so changing
# the domain or toggling sign-in does NOT replace the instance — which would
# take the learner database with it. Change them, apply, then run the
# `apply_config_command` output to restart the app. Adding a new setting
# later means adding a parameter here; user_data needs no edit.
# ---------------------------------------------------------------------------

resource "aws_ssm_parameter" "site_address" {
  name = "${local.ssm_prefix}/SITE_ADDRESS"
  type = "String"
  # Caddy accepts comma-separated hosts. When serving the apex domain we also
  # create a www DNS record (dns.tf) — both must be on the certificate.
  value = var.subdomain == "" ? "${local.fqdn}, www.${var.domain_name}" : local.fqdn
}

resource "aws_ssm_parameter" "base_url" {
  name  = "${local.ssm_prefix}/BASE_URL"
  type  = "String"
  value = local.base_url
}

resource "aws_ssm_parameter" "cookie_secure" {
  name  = "${local.ssm_prefix}/COOKIE_SECURE"
  type  = "String"
  value = "true"
}

resource "aws_ssm_parameter" "allow_anonymous" {
  name  = "${local.ssm_prefix}/ALLOW_ANONYMOUS"
  type  = "String"
  value = var.allow_anonymous ? "true" : "false"
}

resource "aws_ssm_parameter" "pyodide_index_url" {
  name  = "${local.ssm_prefix}/PYODIDE_INDEX_URL"
  type  = "String"
  value = var.pyodide_index_url
}

resource "aws_ssm_parameter" "s3_backup_uri" {
  name  = "${local.ssm_prefix}/S3_BACKUP_URI"
  type  = "String"
  value = var.backup_s3_bucket != "" ? "s3://${var.backup_s3_bucket}/pyforge/${var.environment}/" : ""
}

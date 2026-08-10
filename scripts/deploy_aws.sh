#!/usr/bin/env bash
# One-command AWS deploy for PyForge (after the domain is in Route 53).
#
# Prerequisites:
#   - AWS CLI configured (aws sts get-caller-identity works)
#   - Terraform >= 1.5 on PATH
#   - Domain purchased/registered with a public Route 53 hosted zone
#
# Usage:
#   ./scripts/deploy_aws.sh                 # interactive apply
#   ./scripts/deploy_aws.sh -auto-approve   # non-interactive apply
#
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF="$ROOT/infra/terraform"
AUTO=()
[[ "${1:-}" == "-auto-approve" ]] && AUTO=(-auto-approve)

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1"; exit 1; }; }
need aws
need terraform

echo "==> AWS identity"
aws sts get-caller-identity

if [[ ! -f "$TF/terraform.tfvars" ]]; then
  cp "$TF/terraform.tfvars.example" "$TF/terraform.tfvars"
  echo "Created $TF/terraform.tfvars — edit domain_name, repo_url, budget_alert_email then re-run."
  exit 2
fi

# Fail fast on placeholders
if grep -qE 'domain_name\s*=\s*"(YOUR-DOMAIN|example\.com)' "$TF/terraform.tfvars"; then
  echo "Set a real domain_name in terraform.tfvars first."
  exit 2
fi
if grep -qE 'budget_alert_email\s*=\s*"(YOUR-EMAIL|you@example)' "$TF/terraform.tfvars"; then
  if grep -qE 'monthly_budget_usd\s*=\s*[1-9]' "$TF/terraform.tfvars"; then
    echo "Set budget_alert_email to a real inbox, or monthly_budget_usd = 0."
    exit 2
  fi
fi

DOMAIN="$(grep -E '^\s*domain_name\s*=' "$TF/terraform.tfvars" | head -1 | sed -E 's/.*=\s*"([^"]+)".*/\1/')"
REGION="$(grep -E '^\s*aws_region\s*=' "$TF/terraform.tfvars" | head -1 | sed -E 's/.*=\s*"([^"]+)".*/\1/')"
REGION="${REGION:-us-east-1}"

echo "==> Checking Route 53 hosted zone for $DOMAIN"
if ! aws route53 list-hosted-zones-by-name --dns-name "$DOMAIN." --query "HostedZones[?Name=='${DOMAIN}.'].Id" --output text | grep -q .; then
  echo "No public hosted zone named ${DOMAIN}. Buy the domain in Route 53 (or create a zone and point NS)."
  exit 1
fi

cd "$TF"
echo "==> terraform init"
terraform init -input=false

echo "==> terraform apply"
terraform apply -input=false "${AUTO[@]}"

echo
echo "Deploy submitted. Next:"
echo "  1) Wait ~5 min:  $(terraform output -raw bootstrap_log_command 2>/dev/null || echo 'see terraform output bootstrap_log_command')"
echo "  2) Open:         $(terraform output -raw site_url)"
echo "  3) OAuth later:  create GitHub OAuth app → fill github_client_* → terraform apply → apply_config_command"

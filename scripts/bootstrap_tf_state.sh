#!/usr/bin/env bash
# Create an S3 bucket for Terraform remote state (optional hardening).
#
#   ./scripts/bootstrap_tf_state.sh my-dataforged-tfstate us-east-1
#
set -euo pipefail
BUCKET="${1:?bucket name required}"
REGION="${2:-us-east-1}"

aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
  $([[ "$REGION" == "us-east-1" ]] && echo "" || echo "--create-bucket-configuration LocationConstraint=$REGION")

aws s3api put-bucket-versioning --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$BUCKET" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

TF_DIR="$(cd "$(dirname "$0")/../infra/terraform" && pwd)"
cat > "$TF_DIR/backend.hcl" <<EOF
bucket       = "$BUCKET"
key          = "dataforged/terraform.tfstate"
region       = "$REGION"
encrypt      = true
use_lockfile = true
EOF

echo "Wrote $TF_DIR/backend.hcl"
echo "Next: uncomment backend \"s3\" {} in versions.tf, then:"
echo "  cd infra/terraform && terraform init -migrate-state -backend-config=backend.hcl"

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Default: local state so `terraform init` is non-interactive (one-command
  # first deploy). State contains generated secrets — gitignored here.
  #
  # For anything beyond a personal experiment, switch to S3:
  #   1. Create a bucket (or run scripts/bootstrap_tf_state.sh)
  #   2. Uncomment the backend block below
  #   3. cp backend.hcl.example backend.hcl  # edit bucket/region
  #   4. terraform init -migrate-state -backend-config=backend.hcl
  #
  # backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  # Every resource gets these tags, so you can find (and bill) them later.
  default_tags {
    tags = {
      Project     = "dataforged"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

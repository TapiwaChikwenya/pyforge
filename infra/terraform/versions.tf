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

  # Remote state (recommended for anything beyond a laptop experiment).
  # Partial config — values come from backend.hcl (see backend.hcl.example):
  #
  #   cp backend.hcl.example backend.hcl   # edit bucket/region
  #   terraform init -backend-config=backend.hcl
  #
  # Until you init with a backend config, Terraform uses local state.
  # State contains generated secrets — see README §"A note about state".
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  # Every resource gets these tags, so you can find (and bill) them later.
  default_tags {
    tags = {
      Project   = "pyforge"
      Environment = var.environment
      ManagedBy = "terraform"
    }
  }
}

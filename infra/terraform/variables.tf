# ---------------------------------------------------------------------------
# Everything you need to fill in lives here. Copy terraform.tfvars.example to
# terraform.tfvars and set the values there — don't edit the defaults.
# ---------------------------------------------------------------------------

# --- required ---------------------------------------------------------------

variable "domain_name" {
  description = "Domain you registered in Route 53, e.g. pyforge.dev. A public hosted zone for it must already exist (buying it in Route 53 creates one)."
  type        = string

  validation {
    condition = (
      length(trimspace(var.domain_name)) > 0
      && !startswith(var.domain_name, "http")
      && !contains(["example.com", "example.org", "example.net", "your-domain.com"], var.domain_name)
    )
    error_message = "domain_name must be your real bare domain (e.g. mypyforge.com) — no scheme, no example.com placeholders."
  }
}

# --- naming -----------------------------------------------------------------

variable "subdomain" {
  description = "Host to serve from. Empty string uses the bare domain (pyforge.dev); \"learn\" gives learn.pyforge.dev."
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment tag and SSM parameter namespace. Lets you run prod and staging side by side."
  type        = string
  default     = "prod"
}

# --- AWS placement ----------------------------------------------------------

variable "aws_region" {
  description = "Region to deploy into. Pick one near your learners."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 size. t4g.small (2 vCPU / 2 GiB, Graviton) is the recommended start; t4g.micro works for a small audience."
  type        = string
  default     = "t4g.small"
}

variable "instance_architecture" {
  description = "Must match instance_type. t4g/c7g/m7g/r7g are arm64 (cheaper); t3/t3a/m6i are x86_64."
  type        = string
  default     = "arm64"

  validation {
    condition     = contains(["arm64", "x86_64"], var.instance_architecture)
    error_message = "instance_architecture must be either arm64 or x86_64."
  }
}

variable "root_volume_gb" {
  description = "Root EBS volume size. 20 GB fits the images, the database and room to grow."
  type        = number
  default     = 20
}

# --- application ------------------------------------------------------------

variable "repo_url" {
  description = "Public git URL of your PyForge repo, cloned on boot. Required for one-click deploy (leave empty only if you will upload code manually)."
  type        = string
  default     = ""

  validation {
    condition = (
      var.repo_url == ""
      || (
        startswith(var.repo_url, "https://")
        && !strcontains(var.repo_url, "your-username")
        && endswith(var.repo_url, ".git")
      )
    )
    error_message = "repo_url must be empty (manual upload) or a real https://…/*.git URL — not the your-username placeholder."
  }
}

variable "repo_branch" {
  description = "Branch to deploy."
  type        = string
  default     = "main"
}

variable "github_client_id" {
  description = "GitHub OAuth app client id. Leave empty on the first apply — you need the domain to exist before you can create the OAuth app (see README)."
  type        = string
  default     = ""
}

variable "github_client_secret" {
  description = "GitHub OAuth app client secret."
  type        = string
  default     = ""
  sensitive   = true
}

variable "allow_anonymous" {
  description = "Let visitors use everything without signing in (progress kept in their browser). Recommended true for a public resource."
  type        = bool
  default     = true
}

variable "pyodide_index_url" {
  description = "Where browsers load the Python runtime from. Must be a FULL Pyodide distribution."
  type        = string
  default     = "https://cdn.jsdelivr.net/pyodide/v0.28.3/full/"
}

# --- access -----------------------------------------------------------------

variable "ssh_ingress_cidr" {
  description = "CIDR allowed to reach port 22, e.g. \"203.0.113.4/32\". Leave null to open no SSH at all — use Session Manager instead (the instance role already allows it)."
  type        = string
  default     = null
}

# --- cost guard rail --------------------------------------------------------

variable "monthly_budget_usd" {
  description = "Create an AWS Budget alarm at this monthly spend. Set to 0 to skip."
  type        = number
  default     = 30
}

variable "budget_alert_email" {
  description = "Where budget alerts go. Required if monthly_budget_usd > 0."
  type        = string
  default     = ""

  # Format only. A validation block may not reference another variable before
  # Terraform 1.9, and this config supports >= 1.5, so the "budget requested
  # means an email is required" rule lives in a precondition on the budget
  # resource itself (budget.tf).
  validation {
    condition = (
      var.budget_alert_email == ""
      || (
        length(var.budget_alert_email) > 3
        && strcontains(var.budget_alert_email, "@")
        && !endswith(var.budget_alert_email, "@example.com")
      )
    )
    error_message = "budget_alert_email must be a real inbox — not empty-ish and not an @example.com placeholder. Leave it entirely empty only if monthly_budget_usd = 0."
  }
}

variable "backup_s3_bucket" {
  description = "Optional S3 bucket name for daily Postgres dumps. Empty = local disk backups only on the instance."
  type        = string
  default     = ""
}

variable "data_volume_gb" {
  description = "Extra encrypted EBS volume for Docker volumes (Postgres data). Survives instance replacement when repo_url changes."
  type        = number
  default     = 20
}

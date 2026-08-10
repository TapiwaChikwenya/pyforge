# ---------------------------------------------------------------------------
# One instance running the hosted compose stack, with a stable public address.
# ---------------------------------------------------------------------------

# Always the current Amazon Linux 2023 AMI for the chosen architecture — no
# hardcoded AMI ids to go stale.
data "aws_ssm_parameter" "al2023_ami" {
  name = var.instance_architecture == "arm64" ? "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-arm64" : "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64"
}

resource "aws_instance" "app" {
  ami                    = data.aws_ssm_parameter.al2023_ami.value
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
  iam_instance_profile   = aws_iam_instance_profile.instance.name

  # Only the bootstrap essentials go in here. Everything else (domain, sign-in,
  # runtime URL) is read from SSM at boot, so editing those settings does not
  # replace the instance — and does not destroy the database volume with it.
  # Changing repo_url/branch/region DOES rebuild, which is the intent.
  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/user_data.sh", {
    aws_region  = var.aws_region
    ssm_prefix  = local.ssm_prefix
    repo_url    = var.repo_url
    repo_branch = var.repo_branch
  })

  root_block_device {
    volume_size           = var.root_volume_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  # Require IMDSv2 — blocks the SSRF-to-credentials attack class.
  metadata_options {
    http_tokens                 = "required"
    http_endpoint               = "enabled"
    http_put_response_hop_limit = 2 # containers need one extra hop
  }

  tags = { Name = local.name }

  lifecycle {
    # The AMI parameter moves as Amazon publishes updates; don't rebuild the
    # instance (and lose the database volume) just because of that.
    ignore_changes = [ami]
  }
}

# A fixed IP, so your DNS record stays correct across stop/start.
resource "aws_eip" "app" {
  domain   = "vpc"
  instance = aws_instance.app.id
  tags     = { Name = local.name }

  depends_on = [aws_internet_gateway.this]
}

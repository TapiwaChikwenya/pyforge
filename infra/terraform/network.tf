# ---------------------------------------------------------------------------
# A small dedicated VPC with one public subnet. Deliberately not the default
# VPC: this way the whole deployment is reproducible and `terraform destroy`
# leaves nothing behind.
# ---------------------------------------------------------------------------

locals {
  name = "pyforge-${var.environment}"

  # Host the site answers on: pyforge.dev, or learn.pyforge.dev if a subdomain
  # was given.
  fqdn     = var.subdomain == "" ? var.domain_name : "${var.subdomain}.${var.domain_name}"
  base_url = "https://${local.fqdn}"

  ssm_prefix = "/pyforge/${var.environment}"
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "this" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = local.name }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = local.name }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.20.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = { Name = "${local.name}-public" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = { Name = "${local.name}-public" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ---------------------------------------------------------------------------
# Security group: the web ports, and nothing else unless you ask for SSH.
# Postgres runs in a container on this instance and is never published.
# ---------------------------------------------------------------------------

resource "aws_security_group" "web" {
  name        = "${local.name}-web"
  description = "PyForge web ingress"
  vpc_id      = aws_vpc.this.id

  tags = { Name = "${local.name}-web" }
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.web.id
  description       = "HTTP (Caddy redirects to HTTPS; also used for certificate issuance)"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "https" {
  security_group_id = aws_security_group.web.id
  description       = "HTTPS"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

# Only created when you explicitly set ssh_ingress_cidr. The default is no SSH
# port at all — connect with Session Manager, which needs no open port.
resource "aws_vpc_security_group_ingress_rule" "ssh" {
  count = var.ssh_ingress_cidr == null ? 0 : 1

  security_group_id = aws_security_group.web.id
  description       = "SSH from a single trusted address"
  cidr_ipv4         = var.ssh_ingress_cidr
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.web.id
  description       = "Outbound: image pulls, package installs, GitHub OAuth"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

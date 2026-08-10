# ---------------------------------------------------------------------------
# DNS. Buying the domain in Route 53 creates a public hosted zone for it; this
# looks that zone up and points your host at the instance.
#
# Caddy asks Let's Encrypt for a certificate on the first request, which only
# works once this record resolves — so Terraform creates it before you browse.
# ---------------------------------------------------------------------------

data "aws_route53_zone" "this" {
  name         = "${var.domain_name}."
  private_zone = false
}

resource "aws_route53_record" "app" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = local.fqdn
  type    = "A"
  ttl     = 300
  records = [aws_eip.app.public_ip]
}

# www.<domain> → the same place, but only when serving the bare domain.
resource "aws_route53_record" "www" {
  count = var.subdomain == "" ? 1 : 0

  zone_id = data.aws_route53_zone.this.zone_id
  name    = "www.${var.domain_name}"
  type    = "A"
  ttl     = 300
  records = [aws_eip.app.public_ip]
}

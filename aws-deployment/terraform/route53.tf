# Configuration Route53 pour Plan de Charge

# Zone Route53 existante
data "aws_route53_zone" "main" {
  zone_id = var.hosted_zone_id
}

# Record A principal pointant vers CloudFront
resource "aws_route53_record" "main" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }

  depends_on = [aws_cloudfront_distribution.main]
}

# Record AAAA pour IPv6
resource "aws_route53_record" "main_ipv6" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = false
  }

  depends_on = [aws_cloudfront_distribution.main]
}

# Record pour accès direct à l'ALB (optionnel, pour debug)
resource "aws_route53_record" "alb_direct" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "alb.${data.aws_route53_zone.main.name}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Les certificats sont déjà validés (créés manuellement)
# Pas besoin de validation automatique pour des certificats existants

# Health checks pour monitoring
resource "aws_route53_health_check" "main" {
  fqdn                            = var.domain_name
  port                            = 443
  type                            = "HTTPS"
  resource_path                   = "/health"
  failure_threshold               = 3
  request_interval                = 30

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-health-check"
  })
}

# Outputs pour debugging
output "route53_zone_id" {
  description = "Route53 zone ID"
  value       = data.aws_route53_zone.main.zone_id
}

output "route53_name_servers" {
  description = "Route53 name servers"
  value       = data.aws_route53_zone.main.name_servers
}

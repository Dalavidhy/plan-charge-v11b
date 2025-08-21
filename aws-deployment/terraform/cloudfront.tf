# Configuration CloudFront pour Plan de Charge

# Certificat SSL pour CloudFront (doit être en us-east-1) - utiliser l'ARN directement
locals {
  cloudfront_certificate_arn = "arn:aws:acm:us-east-1:557937909547:certificate/b7c63b81-f120-4348-871e-608bbc29724f"
}

# Distribution CloudFront
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled    = true
  comment            = "Plan de Charge CDN"
  default_root_object = "index.html"
  price_class        = "PriceClass_100"  # USA, Canada, Europe

  aliases = [var.domain_name]

  # Origin ALB (pour l'application complète)
  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    # Headers pour identifier la source
    custom_header {
      name  = "X-Forwarded-Proto"
      value = "https"
    }
  }

  # Comportement par défaut (Frontend SPA)
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "alb-origin"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = ["Host"]

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400  # 1 jour
    max_ttl     = 31536000  # 1 an
  }

  # Comportement pour l'API Backend
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "alb-origin"
    compress               = true
    viewer_protocol_policy = "https-only"

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type", "Accept", "Origin", "Referer", "User-Agent"]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0  # Pas de cache pour l'API
    max_ttl     = 0
  }

  # Comportement pour les docs API
  ordered_cache_behavior {
    path_pattern           = "/docs*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "alb-origin"
    compress               = true
    viewer_protocol_policy = "https-only"

    forwarded_values {
      query_string = false
      headers      = ["Host"]

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600  # 1 heure
    max_ttl     = 86400  # 1 jour
  }

  # Comportement pour les assets statiques
  ordered_cache_behavior {
    path_pattern           = "/assets/*"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "alb-origin"
    compress               = true
    viewer_protocol_policy = "https-only"

    forwarded_values {
      query_string = false
      headers      = []

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 86400     # 1 jour
    default_ttl = 2592000   # 30 jours
    max_ttl     = 31536000  # 1 an
  }

  # Gestion des erreurs pour SPA
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
    error_caching_min_ttl = 300
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
    error_caching_min_ttl = 300
  }

  # Restrictions géographiques
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Certificat SSL
  viewer_certificate {
    acm_certificate_arn      = local.cloudfront_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # WAF Web ACL (à configurer séparément)
  # web_acl_id = aws_wafv2_web_acl.main.arn

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-cloudfront"
  })
}

# Output CloudFront domain
output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront distribution hosted zone ID"
  value       = aws_cloudfront_distribution.main.hosted_zone_id
}

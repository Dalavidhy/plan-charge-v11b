# Outputs pour Plan de Charge

# URLs d'accès
output "application_url" {
  description = "URL principale de l'application"
  value       = "https://${var.domain_name}"
}

output "alb_url" {
  description = "URL directe de l'ALB (pour debug)"
  value       = "https://${aws_lb.main.dns_name}"
}

output "api_url" {
  description = "URL de l'API"
  value       = "https://${var.domain_name}/api/v1"
}

output "docs_url" {
  description = "URL de la documentation API"
  value       = "https://${var.domain_name}/docs"
}

# Infrastructure
output "vpc_id" {
  description = "ID du VPC"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "DNS name de l'ALB"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID de l'ALB"
  value       = aws_lb.main.zone_id
}

# Base de données
output "rds_endpoint" {
  description = "Endpoint RDS"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Endpoint Redis"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  sensitive   = true
}

# ECS
output "ecs_cluster_name" {
  description = "Nom du cluster ECS"
  value       = aws_ecs_cluster.main.name
}

output "backend_service_name" {
  description = "Nom du service backend ECS"
  value       = aws_ecs_service.backend.name
}

output "frontend_service_name" {
  description = "Nom du service frontend ECS"
  value       = aws_ecs_service.frontend.name
}

# CloudFront
output "cloudfront_distribution_id" {
  description = "ID de la distribution CloudFront"
  value       = aws_cloudfront_distribution.main.id
}

# Secrets
output "parameter_store_prefix" {
  description = "Préfixe des paramètres dans Parameter Store"
  value       = "/${var.project_name}/${var.environment}/"
}

# Logging
output "cloudwatch_log_group" {
  description = "Groupe de logs CloudWatch pour ECS"
  value       = aws_cloudwatch_log_group.ecs.name
}

# Monitoring
output "health_check_id" {
  description = "ID du health check Route53"
  value       = aws_route53_health_check.main.id
}

# Security
output "ecr_repositories" {
  description = "URLs des repositories ECR"
  value = {
    backend  = var.backend_image_url
    frontend = var.frontend_image_url
    celery   = var.celery_image_url
  }
}

# Coûts estimés
output "estimated_monthly_cost" {
  description = "Coût mensuel estimé en EUR"
  value = {
    fargate    = "~40 EUR (2x backend + 2x frontend + 1x celery)"
    rds        = "~18 EUR (db.t3.micro, Single-AZ)"
    redis      = "~15 EUR (cache.t3.micro)"
    alb        = "~25 EUR"
    cloudfront = "~5 EUR"
    route53    = "~2 EUR"
    nat_gateway = "~50 EUR"
    total      = "~155 EUR/mois"
    optimized  = "~105 EUR/mois (sans NAT Gateway, avec VPC endpoints)"
  }
}
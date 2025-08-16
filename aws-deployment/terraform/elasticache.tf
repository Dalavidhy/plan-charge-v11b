# Configuration ElastiCache Redis pour Plan de Charge

# Subnet group pour ElastiCache
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-subnet-group"
  })
}

# Parameter group pour optimiser Redis
resource "aws_elasticache_parameter_group" "redis" {
  family = "redis6.x"
  name   = "${local.name_prefix}-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = local.common_tags
}

# Cluster ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${local.name_prefix}-redis"
  engine              = "redis"
  engine_version      = "6.2"
  node_type           = var.redis_node_type
  num_cache_nodes     = 1
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  port                = 6379
  
  # Network
  subnet_group_name   = aws_elasticache_subnet_group.redis.name
  security_group_ids  = [aws_security_group.redis.id]
  
  # Maintenance
  maintenance_window = "sun:05:00-sun:06:00"
  
  # Snapshot (pour sauvegardes)
  snapshot_retention_limit = 3
  snapshot_window         = "02:00-03:00"
  
  # Logs
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow.name
    destination_type = "cloudwatch-logs"
    log_format       = "text"
    log_type         = "slow-log"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis"
  })
}

# CloudWatch Log Group pour Redis
resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/redis/${local.name_prefix}"
  retention_in_days = 7

  tags = local.common_tags
}

# Stockage de l'URL Redis dans Parameter Store
resource "aws_ssm_parameter" "redis_url" {
  name  = "/${var.project_name}/${var.environment}/redis-url"
  type  = "String"
  value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}/0"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-url"
  })
}

# URL Celery broker (même que Redis)
resource "aws_ssm_parameter" "celery_broker_url" {
  name  = "/${var.project_name}/${var.environment}/celery-broker-url"
  type  = "String"
  value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}/0"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-celery-broker-url"
  })
}

# URL Celery result backend
resource "aws_ssm_parameter" "celery_result_backend" {
  name  = "/${var.project_name}/${var.environment}/celery-result-backend"
  type  = "String"
  value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.port}/0"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-celery-result-backend"
  })
}
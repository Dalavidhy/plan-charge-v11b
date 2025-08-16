# Configuration RDS PostgreSQL pour Plan de Charge

# Génération automatique du mot de passe DB
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Subnet group pour RDS
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

# Parameter group pour optimiser PostgreSQL
resource "aws_db_parameter_group" "main" {
  family = "postgres14"
  name   = "${local.name_prefix}-db-params"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"  # Log les requêtes > 1 seconde
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  tags = local.common_tags
}

# Instance RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier = "${local.name_prefix}-db"

  # Engine
  engine         = "postgres"
  engine_version = "14.12"
  instance_class = var.db_instance_class

  # Storage
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2
  storage_encrypted     = true
  storage_type          = "gp3"

  # Database
  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  # Network & Security
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  publicly_accessible    = false

  # Backup & Maintenance
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn
  
  performance_insights_enabled = false  # Pour économiser
  
  # Parameter group
  parameter_group_name = aws_db_parameter_group.main.name

  # Options
  auto_minor_version_upgrade = true
  deletion_protection        = true  # Protection contre suppression accidentelle
  skip_final_snapshot       = false
  final_snapshot_identifier = "${local.name_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-database"
  })

  lifecycle {
    prevent_destroy = true  # Protection supplémentaire
  }
}

# IAM Role pour monitoring RDS
resource "aws_iam_role" "rds_monitoring" {
  name = "${local.name_prefix}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Stockage du mot de passe dans Parameter Store
resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.project_name}/${var.environment}/db-password"
  type  = "SecureString"
  value = random_password.db_password.result

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-db-password"
  })
}

# URL de connexion complète pour l'application
resource "aws_ssm_parameter" "database_url" {
  name = "/${var.project_name}/${var.environment}/database-url"
  type = "SecureString"
  value = "postgresql+asyncpg://${var.db_username}:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/${var.db_name}"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-database-url"
  })
}
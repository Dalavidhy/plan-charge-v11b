# Configuration ECS pour Plan de Charge

# Data sources pour récupérer les paramètres Azure AD
data "aws_ssm_parameter" "azure_client_id" {
  name = "/${var.project_name}/${var.environment}/azure-client-id"
}

data "aws_ssm_parameter" "azure_tenant_id" {
  name = "/${var.project_name}/${var.environment}/azure-tenant-id"
}

data "aws_ssm_parameter" "azure_redirect_uri" {
  name = "/${var.project_name}/${var.environment}/azure-redirect-uri"
}

# Cluster ECS
resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"

      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.ecs.name
      }
    }
  }

  tags = local.common_tags
}

# CloudWatch Log Group pour ECS
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${local.name_prefix}"
  retention_in_days = 7

  tags = local.common_tags
}

# IAM Role pour les tâches ECS
resource "aws_iam_role" "ecs_task_role" {
  name = "${local.name_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Role pour l'exécution des tâches ECS
resource "aws_iam_role" "ecs_execution_role" {
  name = "${local.name_prefix}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Politiques IAM pour le rôle d'exécution
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Politique pour accéder aux Parameter Store
resource "aws_iam_role_policy" "ecs_task_ssm" {
  name = "${local.name_prefix}-ecs-task-ssm-policy"
  role = aws_iam_role.ecs_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/${var.environment}/*"
        ]
      }
    ]
  })
}

# Task Definition Backend
resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name_prefix}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = var.backend_image_url
      
      portMappings = [
        {
          containerPort = 8000
          hostPort     = 8000
          protocol     = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        },
        {
          name  = "CORS_ORIGINS"
          value = "https://${var.domain_name}"
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_ssm_parameter.database_url.arn
        },
        {
          name      = "REDIS_URL"
          valueFrom = aws_ssm_parameter.redis_url.arn
        },
        {
          name      = "CELERY_BROKER_URL"
          valueFrom = aws_ssm_parameter.celery_broker_url.arn
        },
        {
          name      = "CELERY_RESULT_BACKEND"
          valueFrom = aws_ssm_parameter.celery_result_backend.arn
        },
        {
          name      = "JWT_SECRET_KEY"
          valueFrom = aws_ssm_parameter.jwt_secret.arn
        },
        {
          name      = "AZURE_AD_TENANT_ID"
          valueFrom = aws_ssm_parameter.azure_tenant_id.arn
        },
        {
          name      = "AZURE_AD_CLIENT_ID"
          valueFrom = aws_ssm_parameter.azure_client_id.arn
        },
        {
          name      = "AZURE_AD_CLIENT_SECRET"
          valueFrom = aws_ssm_parameter.azure_client_secret.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = local.common_tags
}

# Task Definition Frontend
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "frontend"
      image = var.frontend_image_url
      
      portMappings = [
        {
          containerPort = 80
          hostPort     = 80
          protocol     = "tcp"
        }
      ]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "VITE_AZURE_AD_CLIENT_ID"
          value = data.aws_ssm_parameter.azure_client_id.value
        },
        {
          name  = "VITE_AZURE_AD_TENANT_ID"
          value = data.aws_ssm_parameter.azure_tenant_id.value
        },
        {
          name  = "VITE_AZURE_AD_REDIRECT_URI"
          value = data.aws_ssm_parameter.azure_redirect_uri.value
        },
        {
          name  = "VITE_API_URL"
          value = "/api/v1"
        },
        {
          name  = "VITE_GRYZZLY_USE_MOCK"
          value = "false"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "frontend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }
    }
  ])

  tags = local.common_tags
}

# Task Definition Celery Worker
resource "aws_ecs_task_definition" "celery" {
  family                   = "${local.name_prefix}-celery"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.celery_cpu
  memory                   = var.celery_memory
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "celery-worker"
      image = var.celery_image_url
      
      command = ["celery", "-A", "app.tasks", "worker", "--loglevel=info"]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "AWS_DEFAULT_REGION"
          value = var.aws_region
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_ssm_parameter.database_url.arn
        },
        {
          name      = "REDIS_URL"
          valueFrom = aws_ssm_parameter.redis_url.arn
        },
        {
          name      = "CELERY_BROKER_URL"
          valueFrom = aws_ssm_parameter.celery_broker_url.arn
        },
        {
          name      = "CELERY_RESULT_BACKEND"
          valueFrom = aws_ssm_parameter.celery_result_backend.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "celery"
        }
      }
    },
    {
      name  = "celery-beat"
      image = var.celery_image_url
      
      command = ["celery", "-A", "app.tasks", "beat", "--loglevel=info"]

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_ssm_parameter.database_url.arn
        },
        {
          name      = "REDIS_URL"
          valueFrom = aws_ssm_parameter.redis_url.arn
        },
        {
          name      = "CELERY_BROKER_URL"
          valueFrom = aws_ssm_parameter.celery_broker_url.arn
        },
        {
          name      = "CELERY_RESULT_BACKEND"
          valueFrom = aws_ssm_parameter.celery_result_backend.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "celery-beat"
        }
      }
    }
  ])

  tags = local.common_tags
}
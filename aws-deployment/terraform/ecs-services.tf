# Services ECS pour Plan de Charge

# Service Backend
resource "aws_ecs_service" "backend" {
  name            = "${local.name_prefix}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets         = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  # Auto Scaling
  enable_execute_command = true

  # Attendre que le target group soit créé
  depends_on = [
    aws_lb_listener.http,
    aws_lb_target_group.backend
  ]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-backend-service"
  })
}

# Service Frontend
resource "aws_ecs_service" "frontend" {
  name            = "${local.name_prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets         = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 80
  }

  enable_execute_command = true

  depends_on = [
    aws_lb_listener.http,
    aws_lb_target_group.frontend
  ]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend-service"
  })
}

# Service Celery
resource "aws_ecs_service" "celery" {
  name            = "${local.name_prefix}-celery"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.celery.arn
  desired_count   = var.celery_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets         = aws_subnet.private[*].id
    assign_public_ip = false
  }

  enable_execute_command = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-celery-service"
  })
}

# Auto Scaling pour Backend
resource "aws_appautoscaling_target" "backend" {
  max_capacity       = 10
  min_capacity       = var.backend_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = local.common_tags
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "${local.name_prefix}-backend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

resource "aws_appautoscaling_policy" "backend_memory" {
  name               = "${local.name_prefix}-backend-memory-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 80.0
  }
}

# Auto Scaling pour Frontend
resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = 6
  min_capacity       = var.frontend_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  tags = local.common_tags
}

resource "aws_appautoscaling_policy" "frontend_cpu" {
  name               = "${local.name_prefix}-frontend-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
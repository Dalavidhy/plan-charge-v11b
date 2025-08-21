# Variables pour le déploiement Plan de Charge

variable "aws_region" {
  description = "Région AWS pour le déploiement"
  type        = string
  default     = "eu-west-3"
}

variable "environment" {
  description = "Environnement de déploiement"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Nom du projet"
  type        = string
  default     = "plan-charge"
}

variable "domain_name" {
  description = "Nom de domaine de l'application"
  type        = string
  default     = "plan-de-charge.aws.nda-partners.com"
}

variable "hosted_zone_id" {
  description = "ID de la zone Route53 pour aws.nda-partners.com"
  type        = string
  default     = "Z03619201TLOZ0RGN61SR"
}

# Configuration VPC
variable "vpc_cidr" {
  description = "CIDR block pour le VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks pour les subnets privés"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks pour les subnets publics"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

# Configuration RDS
variable "db_instance_class" {
  description = "Instance class pour RDS"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Stockage alloué pour RDS (GB)"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Nom de la base de données"
  type        = string
  default     = "plancharge"
}

variable "db_username" {
  description = "Username pour RDS"
  type        = string
  default     = "plancharge"
}

# Configuration ElastiCache
variable "redis_node_type" {
  description = "Type de nœud pour ElastiCache Redis"
  type        = string
  default     = "cache.t3.micro"
}

# Configuration ECS
variable "backend_cpu" {
  description = "CPU pour le service backend ECS"
  type        = number
  default     = 512
}

variable "backend_memory" {
  description = "Mémoire pour le service backend ECS"
  type        = number
  default     = 1024
}

variable "backend_desired_count" {
  description = "Nombre désiré de tâches backend"
  type        = number
  default     = 2
}

variable "frontend_cpu" {
  description = "CPU pour le service frontend ECS"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Mémoire pour le service frontend ECS"
  type        = number
  default     = 512
}

variable "frontend_desired_count" {
  description = "Nombre désiré de tâches frontend"
  type        = number
  default     = 2
}

variable "celery_cpu" {
  description = "CPU pour le service Celery ECS"
  type        = number
  default     = 256
}

variable "celery_memory" {
  description = "Mémoire pour le service Celery ECS"
  type        = number
  default     = 512
}

variable "celery_desired_count" {
  description = "Nombre désiré de tâches Celery"
  type        = number
  default     = 1
}

# URLs des images ECR
variable "backend_image_url" {
  description = "URL de l'image Docker backend dans ECR"
  type        = string
  default     = "557937909547.dkr.ecr.eu-west-3.amazonaws.com/plan-charge-backend:latest"
}

variable "frontend_image_url" {
  description = "URL de l'image Docker frontend dans ECR"
  type        = string
  default     = "557937909547.dkr.ecr.eu-west-3.amazonaws.com/plan-charge-frontend:latest"
}

variable "celery_image_url" {
  description = "URL de l'image Docker Celery dans ECR"
  type        = string
  default     = "557937909547.dkr.ecr.eu-west-3.amazonaws.com/plan-charge-celery:latest"
}

# Secrets (à passer via variables d'environnement ou fichier tfvars)
variable "jwt_secret_key" {
  description = "Clé secrète pour JWT"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_ad_tenant_id" {
  description = "Tenant ID Azure AD"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_ad_client_id" {
  description = "Client ID Azure AD"
  type        = string
  sensitive   = true
  default     = ""
}

variable "azure_ad_client_secret" {
  description = "Client Secret Azure AD"
  type        = string
  sensitive   = true
  default     = ""
}

variable "payfit_api_key" {
  description = "Clé API PayFit"
  type        = string
  sensitive   = true
  default     = ""
}

variable "gryzzly_api_key" {
  description = "Clé API Gryzzly"
  type        = string
  sensitive   = true
  default     = ""
}

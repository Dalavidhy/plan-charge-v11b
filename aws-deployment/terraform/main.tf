# Configuration Terraform pour Plan de Charge
# Région : eu-west-3 (Paris)

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend S3 pour le state (à créer manuellement)
  # backend "s3" {
  #   bucket = "nda-terraform-state-eu-west-3"
  #   key    = "plan-charge/terraform.tfstate"
  #   region = "eu-west-3"
  # }
}

# Configuration des providers
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Plan-Charge"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "NDA-Partners"
    }
  }
}

# Provider pour les certificats CloudFront (us-east-1 obligatoire)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "Plan-Charge"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "NDA-Partners"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Variables locales
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "NDA-Partners"
  }
}

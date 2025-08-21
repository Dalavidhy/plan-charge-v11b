# Configuration des secrets dans AWS Parameter Store

# JWT Secret Key (généré automatiquement si non fourni)
resource "random_password" "jwt_secret" {
  length  = 32
  special = true

  # Utiliser la variable fournie ou générer automatiquement
  keepers = {
    provided_secret = var.jwt_secret_key != "" ? var.jwt_secret_key : null
  }
}

resource "aws_ssm_parameter" "jwt_secret" {
  name  = "/${var.project_name}/${var.environment}/jwt-secret"
  type  = "SecureString"
  value = var.jwt_secret_key != "" ? var.jwt_secret_key : random_password.jwt_secret.result

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-jwt-secret"
  })
}

# Azure AD Configuration
resource "aws_ssm_parameter" "azure_tenant_id" {
  name  = "/${var.project_name}/${var.environment}/azure-tenant-id"
  type  = "String"
  value = var.azure_ad_tenant_id != "" ? var.azure_ad_tenant_id : "placeholder-tenant-id"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-azure-tenant-id"
  })
}

resource "aws_ssm_parameter" "azure_client_id" {
  name  = "/${var.project_name}/${var.environment}/azure-client-id"
  type  = "String"
  value = var.azure_ad_client_id != "" ? var.azure_ad_client_id : "placeholder-client-id"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-azure-client-id"
  })
}

resource "aws_ssm_parameter" "azure_client_secret" {
  name  = "/${var.project_name}/${var.environment}/azure-client-secret"
  type  = "SecureString"
  value = var.azure_ad_client_secret != "" ? var.azure_ad_client_secret : "placeholder-client-secret"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-azure-client-secret"
  })
}

# Azure AD Redirect URI
resource "aws_ssm_parameter" "azure_redirect_uri" {
  name  = "/${var.project_name}/${var.environment}/azure-redirect-uri"
  type  = "String"
  value = "https://${var.domain_name}/auth/callback"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-azure-redirect-uri"
  })
}

# API Keys externes
resource "aws_ssm_parameter" "payfit_api_key" {
  name  = "/${var.project_name}/${var.environment}/payfit-api-key"
  type  = "SecureString"
  value = var.payfit_api_key != "" ? var.payfit_api_key : "placeholder-payfit-key"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-payfit-api-key"
  })
}

resource "aws_ssm_parameter" "gryzzly_api_key" {
  name  = "/${var.project_name}/${var.environment}/gryzzly-api-key"
  type  = "SecureString"
  value = var.gryzzly_api_key != "" ? var.gryzzly_api_key : "placeholder-gryzzly-key"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-gryzzly-api-key"
  })
}

# URLs des APIs externes
resource "aws_ssm_parameter" "payfit_api_url" {
  name  = "/${var.project_name}/${var.environment}/payfit-api-url"
  type  = "String"
  value = "https://partner-api.payfit.com"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-payfit-api-url"
  })
}

resource "aws_ssm_parameter" "gryzzly_api_url" {
  name  = "/${var.project_name}/${var.environment}/gryzzly-api-url"
  type  = "String"
  value = "https://api.gryzzly.io/v1"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-gryzzly-api-url"
  })
}

# Configuration de l'application
resource "aws_ssm_parameter" "app_name" {
  name  = "/${var.project_name}/${var.environment}/app-name"
  type  = "String"
  value = "Plan Charge"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-app-name"
  })
}

resource "aws_ssm_parameter" "app_url" {
  name  = "/${var.project_name}/${var.environment}/app-url"
  type  = "String"
  value = "https://${var.domain_name}"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-app-url"
  })
}

# Configuration des features
resource "aws_ssm_parameter" "feature_sso" {
  name  = "/${var.project_name}/${var.environment}/feature-sso"
  type  = "String"
  value = "true"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-feature-sso"
  })
}

resource "aws_ssm_parameter" "sso_mandatory" {
  name  = "/${var.project_name}/${var.environment}/sso-mandatory"
  type  = "String"
  value = "true"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-sso-mandatory"
  })
}

resource "aws_ssm_parameter" "sso_allowed_domains" {
  name  = "/${var.project_name}/${var.environment}/sso-allowed-domains"
  type  = "String"
  value = "nda-partners.com"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-sso-allowed-domains"
  })
}

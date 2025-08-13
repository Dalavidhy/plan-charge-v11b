"""Application configuration."""

from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Plan Charge v9"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: RedisDsn
    REDIS_POOL_SIZE: int = 10
    REDIS_DECODE_RESPONSES: bool = True
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_TIMEOUT: int = 5
    
    # Celery
    CELERY_BROKER_URL: RedisDsn
    CELERY_RESULT_BACKEND: RedisDsn
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_TASK_EAGER_PROPAGATES: bool = False
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = []
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # File Storage
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "plancharge-attachments"
    S3_REGION: str = "eu-west-1"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", 
        ".png", ".jpg", ".jpeg", ".gif", ".csv"
    ]
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@plancharge.example.com"
    EMAIL_ENABLED: bool = False
    
    # External Integrations
    PAYFIT_API_URL: str = "https://partner-api.payfit.com"
    PAYFIT_API_KEY: Optional[str] = None
    PAYFIT_COMPANY_ID: Optional[str] = None
    
    GRYZZLY_API_URL: str = "https://api.gryzzly.com/v1"
    GRYZZLY_API_KEY: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"
    LOG_CORRELATION_ID_HEADER: str = "X-Request-ID"
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090
    
    # Feature Flags
    FEATURE_BULK_IMPORT: bool = True
    FEATURE_ADVANCED_REPORTS: bool = True
    FEATURE_INTEGRATIONS: bool = True
    FEATURE_WEBHOOKS: bool = False
    FEATURE_SSO: bool = False
    FEATURE_WHAT_IF_SCENARIOS: bool = False
    
    # Performance
    CACHE_TTL_DEFAULT: int = 300  # 5 minutes
    CACHE_TTL_REPORTS: int = 900  # 15 minutes
    CACHE_TTL_STATIC: int = 3600  # 1 hour
    
    # Business Rules
    MAX_ALLOCATION_PERCENTAGE: int = 200  # Allow up to 200% allocation for detection
    MIN_HOURS_PER_WEEK: float = 0.5
    MAX_HOURS_PER_WEEK: float = 60.0
    DEFAULT_WORKWEEK_HOURS: float = 35.0  # French standard
    SURALLOCATION_THRESHOLD: float = 100.0  # Percentage
    
    # Calculation Settings
    WEEK_START_DAY: int = 0  # 0 = Monday, 6 = Sunday
    FISCAL_YEAR_START_MONTH: int = 1  # January
    DEFAULT_TIMEZONE: str = "Europe/Paris"
    
    # Audit & Retention
    AUDIT_LOG_RETENTION_DAYS: int = 365
    SOFT_DELETE_RETENTION_DAYS: int = 30
    SESSION_RETENTION_DAYS: int = 90
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return str(self.DATABASE_URL).replace("+asyncpg", "")
    
    def get_feature_flag(self, flag_name: str) -> bool:
        """Get feature flag value."""
        return getattr(self, f"FEATURE_{flag_name.upper()}", False)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
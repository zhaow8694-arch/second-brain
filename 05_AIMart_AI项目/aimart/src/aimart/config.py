"""AIMart configuration module.

All settings are loaded from environment variables with sensible defaults.
Uses pydantic-settings for validation and type coercion.
"""

from enum import StrEnum
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment."""

    DEV = "dev"
    STAGING = "staging"
    PRE_PROD = "pre-prod"
    PROD = "prod"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="AIMART_",
    )

    # --- Application ---
    environment: Environment = Environment.DEV
    app_name: str = "AIMart"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # --- Database (PostgreSQL) ---
    database_url: str = "postgresql+asyncpg://aimart:aimart@localhost:5432/aimart"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_pool_recycle: int = 3600

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str | None = None

    # --- Kafka ---
    kafka_brokers: str = "localhost:9092"
    kafka_topic_prefix: str = "aimart"

    # --- ClickHouse ---
    clickhouse_url: str = "clickhouse://localhost:9000/default"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""

    # --- Elasticsearch ---
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_api_key: str | None = None

    # --- JWT Authentication ---
    jwt_algorithm: str = "RS256"
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"
    jwt_access_token_ttl: int = 60  # minutes
    jwt_refresh_token_ttl: int = 43200  # minutes (30 days)
    jwt_issuer: str = "aimart"

    # --- Rate Limiting ---
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    rate_limit_authenticated: str = "300/minute"
    rate_limit_storage_uri: str = "redis://localhost:6379/1"

    # --- CORS ---
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allowed_methods: list[str] = ["*"]
    cors_allowed_headers: list[str] = ["*"]

    # --- MinIO (Object Storage) ---
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "aimart"
    minio_secure: bool = False

    # --- Web3 / Blockchain ---
    web3_provider_url: str = "http://localhost:8545"
    web3_contract_address: str | None = None

    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Normalize environment value."""
        return v.lower().strip()

    @field_validator("database_url", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure asyncpg driver is used."""
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PROD

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEV


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()

"""App configuration — loads from .env via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Runtime environment
    environment: str = "local"  # local | staging | production

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    secret_key: str = "CHANGE_ME_SECRET_KEY_64PLUS_CHARS"
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"
    auth_username: str = "admin"
    auth_password: str = "CHANGE_ME_AUTH_PASSWORD"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    secure_cookies: bool = False

    # Security hardening
    allow_localhost_cors_in_non_local: bool = False
    enforce_strong_secrets: bool = True

    # Rate limiting
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests_local: int = 100
    rate_limit_max_requests_non_local: int = 60

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "obelisk"
    postgres_user: str = "obelisk"
    postgres_password: str = "obelisk"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Registry APIs
    npm_registry_url: str = "https://registry.npmjs.org"
    pypi_registry_url: str = "https://pypi.org/pypi"

    # ML model paths
    codebert_model_path: str = "ml_models/saved_models/codebert"
    gnn_model_path: str = "ml_models/saved_models/gnn"
    isolation_forest_path: str = "ml_models/saved_models/isolation_forest"

    # Sandbox
    sandbox_timeout: int = 300
    sandbox_memory_limit: str = "512m"
    sandbox_enabled: bool = False
    sandbox_release_track: str = "v1.1"
    sandbox_allow_docker: bool = False

    # Readiness / startup safety
    enable_startup_readiness_checks: bool = True
    startup_check_dependencies: bool = False
    strict_startup_checks: bool = False

    # Worker observability
    worker_health_check_timeout_s: float = 1.5

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()

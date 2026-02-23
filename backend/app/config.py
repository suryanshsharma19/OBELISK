"""Configuration management for OBELISK."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    secret_key: str = "change-me-in-production"

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

"""
Configuration management module

Uses pydantic-settings to manage configuration, supports reading from environment variables and .env files
"""

from functools import lru_cache
from typing import Dict, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ======================
    # Database Configuration
    # ======================
    mysql_host: str = Field(default="localhost", description="MySQL host")
    mysql_port: int = Field(default=3306, description="MySQL port")
    mysql_user: str = Field(default="sag", description="MySQL user")
    mysql_password: str = Field(default="sag_pass", description="MySQL password")
    mysql_database: str = Field(default="sag", description="MySQL database name")

    # ======================
    # Elasticsearch Configuration
    # ======================
    es_host: str = Field(default="localhost", description="Elasticsearch host")
    es_port: int = Field(default=9200, description="Elasticsearch port")
    es_username: Optional[str] = Field(default="elastic", description="Elasticsearch username")
    es_password: Optional[str] = Field(
        default=None,
        description="Elasticsearch password",
        validation_alias="ELASTIC_PASSWORD"
    )

    # ======================
    # Redis Configuration
    # ======================
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database")

    # ======================
    # LLM Configuration (uses proxy API or OpenAI official)
    # ======================
    llm_api_key: str = Field(default="", description="LLM API key")
    llm_model: str = Field(default="sophnet/Qwen3-30B-A3B-Thinking-2507", description="LLM model")
    llm_base_url: Optional[str] = Field(
        default=None, description="LLM API base URL (leave empty to use OpenAI official)"
    )
    
    # LLM behavior parameters (default values for all calls, can be overridden by database config)
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature parameter")
    llm_max_tokens: int = Field(default=8000, ge=1, description="LLM maximum output tokens")
    llm_top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="LLM top_p parameter")
    llm_frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    llm_presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    
    # LLM reliability parameters
    llm_timeout: int = Field(default=600, ge=1, description="LLM timeout (seconds)")
    llm_max_retries: int = Field(default=3, ge=0, description="LLM maximum retry count")
    
    # Database configuration switch
    use_db_config: bool = Field(default=True, description="Whether to use database configuration")

    # ======================
    # Embedding Configuration (uses proxy API or OpenAI official)
    # ======================
    embedding_api_key: str = Field(
        default="", description="Embedding API key (leave empty to use llm_api_key)"
    )
    embedding_model_name: str = Field(default="Qwen/Qwen3-Embedding-0.6B", description="Embedding model")
    embedding_dimensions: Optional[int] = Field(
        default=None,
        description="Embedding dimensions (optional, leave empty to use model default. text-embedding-3-small default 1536, text-embedding-3-large default 3072)",
    )
    embedding_base_url: Optional[str] = Field(
        default=None, description="Embedding API base URL (leave empty to use llm_base_url)"
    )

    # ======================
    # Application Configuration
    # ======================
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format")

    # ======================
    # API Configuration
    # ======================
    api_host: str = Field(default="0.0.0.0", description="API service address")
    api_port: int = Field(default=8000, description="API service port")
    api_workers: int = Field(default=4, description="API worker count")

    # ======================
    # File Upload Configuration
    # ======================
    upload_dir: str = Field(default="./uploads", description="Upload file directory")
    max_upload_size: int = Field(
        default=100 * 1024 * 1024, description="Maximum upload size (bytes, default 100MB)"
    )

    # Entity weight configuration
    # entity_weights: str = Field(
    #     default="time:0.9,location:1.0,person:1.1,topic:1.5,action:1.2,tags:1.0",
    #     description="Entity type weights",
    # )

    # ======================
    # Performance Configuration
    # ======================
    db_pool_size: int = Field(default=10, description="Database connection pool size")
    db_max_overflow: int = Field(default=20, description="Database connection pool max overflow")
    db_pool_recycle: int = Field(default=3600, description="Database connection recycle time (seconds)")

    # Cache TTL
    cache_entity_ttl: int = Field(default=86400, description="Entity cache TTL (seconds)")
    cache_llm_ttl: int = Field(default=604800, description="LLM cache TTL (seconds)")
    cache_search_ttl: int = Field(default=3600, description="Search cache TTL (seconds)")

    @property
    def mysql_url(self) -> str:
        """MySQL connection URL"""
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    @property
    def elasticsearch_url(self) -> str:
        """Elasticsearch connection URL"""
        return f"http://{self.es_host}:{self.es_port}"

    @property
    def es_url(self) -> str:
        """Elasticsearch connection URL (compatible with old version)"""
        return self.elasticsearch_url

    # @property
    # def entity_weights_dict(self) -> Dict[str, float]:
    #     """Entity weights dictionary"""
    #     result = {}
    #     for pair in self.entity_weights.split(","):
    #         if ":" in pair:
    #             key, value = pair.split(":")
    #             try:
    #                 result[key.strip()] = float(value.strip())
    #             except ValueError:
    #                 continue
    #     return result

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of: {', '.join(allowed)}")
        return v.upper()


@lru_cache()
def get_settings() -> Settings:
    """Get configuration singleton"""
    return Settings()

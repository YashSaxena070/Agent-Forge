"""
Shared configuration management for AgentForge.
"""
import os
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Environment
    ENVIRONMENT: str = Field(default="development", description="Runtime environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Database
    POSTGRES_PASSWORD: str = Field(default="agentforge_dev", description="PostgreSQL password")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://agentforge:agentforge_dev@localhost:5432/agentforge",
        description="Async PostgreSQL connection URL"
    )
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    
    # Qdrant
    QDRANT_URL: str = Field(default="http://localhost:6333", description="Qdrant HTTP endpoint")
    QDRANT_API_KEY: Optional[str] = Field(default=None, description="Qdrant API key")
    
    # Neo4j
    NEO4J_PASSWORD: str = Field(default="agentforge_dev", description="Neo4j password")
    NEO4J_URI: str = Field(default="bolt://localhost:7687", description="Neo4j Bolt URI")
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j username")
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", description="Kafka bootstrap servers")
    
    # Temporal
    TEMPORAL_ADDRESS: str = Field(default="localhost:7233", description="Temporal gRPC address")
    
    # MinIO
    MINIO_ENDPOINT: str = Field(default="localhost:9000", description="MinIO endpoint")
    MINIO_ACCESS_KEY: str = Field(default="agentforge", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="agentforge_dev", description="MinIO secret key")
    MINIO_BUCKET: str = Field(default="agentforge-artifacts", description="MinIO bucket name")
    
    # OpenTelemetry
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(default="http://localhost:4317", description="OTLP endpoint")
    OTEL_SERVICE_NAME: str = Field(default="agentforge-backend", description="Service name for telemetry")
    
    # LLM Providers (Default: Groq)
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI or Groq API key")
    OPENAI_BASE_URL: Optional[str] = Field(default="https://api.groq.com/openai/v1", description="OpenAI or Groq base URL")
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google API key")
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None, description="Azure OpenAI API key")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, description="Azure OpenAI endpoint")
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = Field(default=None, description="Azure OpenAI deployment name")
    
    DEFAULT_LLM_PROVIDER: str = Field(default="groq", description="Default LLM provider")
    DEFAULT_LLM_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Default LLM model (e.g. llama-3.3-70b-versatile, gpt-110b)")
    DEFAULT_EMBEDDING_MODEL: str = Field(default="text-embedding-3-large", description="Default embedding model")
    
    # GitHub
    GITHUB_TOKEN: Optional[str] = Field(default=None, description="GitHub personal access token")
    GITHUB_WEBHOOK_SECRET: Optional[str] = Field(default=None, description="GitHub webhook secret")
    
    # Docker
    DOCKER_HOST: str = Field(default="unix:///var/run/docker.sock", description="Docker daemon socket")
    
    # Kubernetes
    KUBECONFIG: Optional[str] = Field(default=None, description="Path to kubeconfig file")
    
    # Security
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production-min-32-chars",
        description="Secret key for JWT signing"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT expiration in hours")
    REFRESH_TOKEN_EXPIRATION_DAYS: int = Field(default=30, description="Refresh token expiration in days")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Max requests per window")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, description="Rate limit window in seconds")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins"
    )
    
    # Email
    SMTP_HOST: Optional[str] = Field(default=None, description="SMTP host")
    SMTP_PORT: int = Field(default=587, description="SMTP port")
    SMTP_USER: Optional[str] = Field(default=None, description="SMTP username")
    SMTP_PASSWORD: Optional[str] = Field(default=None, description="SMTP password")
    SMTP_FROM: str = Field(default="noreply@agentforge.local", description="From email address")
    
    # Slack
    SLACK_WEBHOOK_URL: Optional[str] = Field(default=None, description="Slack webhook URL")
    SLACK_BOT_TOKEN: Optional[str] = Field(default=None, description="Slack bot token")
    
    # Monitoring
    GRAFANA_PASSWORD: str = Field(default="admin", description="Grafana admin password")
    PROMETHEUS_RETENTION_DAYS: int = Field(default=30, description="Prometheus retention days")
    
    # Feature Flags
    ENABLE_MCP: bool = Field(default=True, description="Enable MCP integrations")
    ENABLE_TEMPORAL: bool = Field(default=True, description="Enable Temporal workflows")
    ENABLE_KAFKA: bool = Field(default=True, description="Enable Kafka event streaming")
    ENABLE_RAG: bool = Field(default=True, description="Enable RAG pipeline")
    ENABLE_MEMORY: bool = Field(default=True, description="Enable memory layer")
    
    # MCP Servers
    MCP_GITHUB_ENABLED: bool = Field(default=True, description="Enable GitHub MCP")
    MCP_DOCKER_ENABLED: bool = Field(default=True, description="Enable Docker MCP")
    MCP_KUBERNETES_ENABLED: bool = Field(default=True, description="Enable Kubernetes MCP")
    MCP_FILESYSTEM_ENABLED: bool = Field(default=True, description="Enable Filesystem MCP")
    MCP_BROWSER_ENABLED: bool = Field(default=True, description="Enable Browser MCP")
    MCP_ISSUE_TRACKER_ENABLED: bool = Field(default=True, description="Enable Issue Tracker MCP")
    MCP_DOCS_ENABLED: bool = Field(default=True, description="Enable Documentation MCP")
    
    # Agent Configuration
    PLANNER_MAX_ITERATIONS: int = Field(default=5, description="Max planner iterations")
    AGENT_TIMEOUT_SECONDS: int = Field(default=300, description="Agent execution timeout")
    MAX_CONCURRENT_AGENTS: int = Field(default=10, description="Max concurrent agents")
    
    # RAG Configuration
    RAG_CHUNK_SIZE: int = Field(default=1000, description="RAG chunk size")
    RAG_CHUNK_OVERLAP: int = Field(default=200, description="RAG chunk overlap")
    RAG_TOP_K: int = Field(default=10, description="RAG top-k retrieval")
    RAG_RERANK_TOP_K: int = Field(default=5, description="RAG rerank top-k")
    RAG_SIMILARITY_THRESHOLD: float = Field(default=0.7, description="RAG similarity threshold")
    
    # Memory Configuration
    SHORT_TERM_TTL_HOURS: int = Field(default=24, description="Short-term memory TTL in hours")
    LONG_TERM_RETENTION_DAYS: int = Field(default=365, description="Long-term retention in days")
    SEMANTIC_MEMORY_MAX_ENTRIES: int = Field(default=10000, description="Max semantic memory entries")
    RELATIONSHIP_MEMORY_MAX_DEPTH: int = Field(default=3, description="Max relationship depth")
    
    # Deployment
    DEPLOYMENT_NAMESPACE: str = Field(default="agentforge", description="Kubernetes namespace")
    DEPLOYMENT_CLUSTER: str = Field(default="local", description="Target cluster name")
    
    # Vault
    VAULT_URL: str = Field(default="http://localhost:8200", description="Vault server URL")
    VAULT_TOKEN: Optional[str] = Field(default=None, description="Vault authentication token")
    VAULT_NAMESPACE: Optional[str] = Field(default=None, description="Vault namespace")
    VAULT_MOUNT_POINT: str = Field(default="secret", description="Vault KV mount point")
    
    # Encryption
    ENCRYPTION_KEY: str = Field(
        default="your-32-byte-encryption-key-change-in-production",
        description="32-byte encryption key for secret encryption"
    )
    
    # OPA
    OPA_URL: str = Field(default="http://localhost:8181", description="OPA server URL")
    OPA_TOKEN: Optional[str] = Field(default=None, description="OPA authentication token")
    
    # SSO/OIDC
    OIDC_ISSUER: Optional[str] = Field(default=None, description="OIDC issuer URL")
    OIDC_CLIENT_ID: Optional[str] = Field(default=None, description="OIDC client ID")
    OIDC_CLIENT_SECRET: Optional[str] = Field(default=None, description="OIDC client secret")
    OIDC_REDIRECT_URI: Optional[str] = Field(default=None, description="OIDC redirect URI")
    
    # SAML
    SAML_ENTITY_ID: Optional[str] = Field(default=None, description="SAML entity ID")
    SAML_SSO_URL: Optional[str] = Field(default=None, description="SAML SSO URL")
    SAML_SLO_URL: Optional[str] = Field(default=None, description="SAML SLO URL")
    SAML_X509_CERT: Optional[str] = Field(default=None, description="SAML X.509 certificate")
    SAML_ACS_URL: Optional[str] = Field(default=None, description="SAML ACS URL")
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() == "testing"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
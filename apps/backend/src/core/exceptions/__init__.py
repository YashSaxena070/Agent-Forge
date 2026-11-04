"""
Backend-specific exceptions extending shared exceptions.
"""
from services.shared.exceptions import (
    AgentForgeException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ExternalServiceError,
    LLMError,
    DatabaseError,
    WorkflowError,
    AgentError,
    MCPError,
    RAGError,
    MemoryError,
    DeploymentError,
    TemporalError,
    KafkaError,
    ConfigurationError,
)

# Re-export all shared exceptions
__all__ = [
    "AgentForgeException",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ExternalServiceError",
    "LLMError",
    "DatabaseError",
    "WorkflowError",
    "AgentError",
    "MCPError",
    "RAGError",
    "MemoryError",
    "DeploymentError",
    "TemporalError",
    "KafkaError",
    "ConfigurationError",
]
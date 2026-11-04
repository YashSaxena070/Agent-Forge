"""
Shared exception hierarchy for AgentForge.
"""
from typing import Any, Dict, Optional
from uuid import UUID


class AgentForgeException(Exception):
    """Base exception for all AgentForge errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(AgentForgeException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
            status_code=400,
        )


class AuthenticationError(AgentForgeException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            details=details or {},
            status_code=401,
        )


class AuthorizationError(AgentForgeException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            details=details or {},
            status_code=403,
        )


class NotFoundError(AgentForgeException):
    """Raised when a resource is not found."""
    
    def __init__(
        self,
        resource: str,
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            details={"resource": resource, "resource_id": str(resource_id) if resource_id else None, **(details or {})},
            status_code=404,
        )


class ConflictError(AgentForgeException):
    """Raised when a resource conflict occurs."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            details=details or {},
            status_code=409,
        )


class RateLimitError(AgentForgeException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after} if retry_after else {},
            status_code=429,
        )


class ExternalServiceError(AgentForgeException):
    """Raised when an external service call fails."""
    
    def __init__(
        self,
        service: str,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{service} error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "status_code": status_code, **(details or {})},
            status_code=502,
        )


class LLMError(ExternalServiceError):
    """Raised when LLM API call fails."""
    
    def __init__(
        self,
        provider: str,
        message: str,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            service=f"LLM ({provider})",
            message=message,
            details={"provider": provider, "model": model, **(details or {})},
        )


class DatabaseError(AgentForgeException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details={"operation": operation, **(details or {})},
            status_code=500,
        )


class WorkflowError(AgentForgeException):
    """Raised when workflow execution fails."""
    
    def __init__(
        self,
        message: str,
        workflow_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        phase: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="WORKFLOW_ERROR",
            details={
                "workflow_id": str(workflow_id) if workflow_id else None,
                "task_id": str(task_id) if task_id else None,
                "phase": phase,
                **(details or {}),
            },
            status_code=500,
        )


class AgentError(AgentForgeException):
    """Raised when agent execution fails."""
    
    def __init__(
        self,
        message: str,
        agent_role: Optional[str] = None,
        task_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="AGENT_ERROR",
            details={
                "agent_role": agent_role,
                "task_id": str(task_id) if task_id else None,
                **(details or {}),
            },
            status_code=500,
        )


class MCPError(AgentForgeException):
    """Raised when MCP tool invocation fails."""
    
    def __init__(
        self,
        tool: str,
        message: str,
        server: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"MCP tool '{tool}' error: {message}",
            code="MCP_ERROR",
            details={"tool": tool, "server": server, **(details or {})},
            status_code=500,
        )


class RAGError(AgentForgeException):
    """Raised when RAG pipeline fails."""
    
    def __init__(
        self,
        message: str,
        stage: Optional[str] = None,
        query: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="RAG_ERROR",
            details={"stage": stage, "query": query, **(details or {})},
            status_code=500,
        )


class MemoryError(AgentForgeException):
    """Raised when memory operation fails."""
    
    def __init__(
        self,
        message: str,
        memory_type: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="MEMORY_ERROR",
            details={"memory_type": memory_type, "operation": operation, **(details or {})},
            status_code=500,
        )


class DeploymentError(AgentForgeException):
    """Raised when deployment fails."""
    
    def __init__(
        self,
        message: str,
        deployment_id: Optional[UUID] = None,
        environment: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="DEPLOYMENT_ERROR",
            details={
                "deployment_id": str(deployment_id) if deployment_id else None,
                "environment": environment,
                **(details or {}),
            },
            status_code=500,
        )


class TemporalError(AgentForgeException):
    """Raised when Temporal workflow/activity fails."""
    
    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        run_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="TEMPORAL_ERROR",
            details={
                "workflow_id": workflow_id,
                "run_id": run_id,
                "activity_id": activity_id,
                **(details or {}),
            },
            status_code=500,
        )


class KafkaError(AgentForgeException):
    """Raised when Kafka operation fails."""
    
    def __init__(
        self,
        message: str,
        topic: Optional[str] = None,
        partition: Optional[int] = None,
        offset: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="KAFKA_ERROR",
            details={"topic": topic, "partition": partition, "offset": offset, **(details or {})},
            status_code=500,
        )


class ConfigurationError(AgentForgeException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key, **(details or {})},
            status_code=500,
        )
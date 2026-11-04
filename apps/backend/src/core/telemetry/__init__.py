"""
Backend-specific telemetry initialization.
"""
from services.shared.telemetry import (
    init_telemetry,
    get_tracer,
    get_meter,
    traced,
    trace_span,
    record_workflow_metrics,
    record_task_metrics,
    record_agent_metrics,
    record_rag_metrics,
    record_memory_metrics,
    record_error,
    shutdown_telemetry,
)

from apps.backend.src.core.config import settings


def init_backend_telemetry() -> None:
    """Initialize telemetry for backend service."""
    init_telemetry(service_name="agentforge-backend")


__all__ = [
    "init_backend_telemetry",
    "get_tracer",
    "get_meter",
    "traced",
    "trace_span",
    "record_workflow_metrics",
    "record_task_metrics",
    "record_agent_metrics",
    "record_rag_metrics",
    "record_memory_metrics",
    "record_error",
    "shutdown_telemetry",
]
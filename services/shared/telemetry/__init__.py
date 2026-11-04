"""
OpenTelemetry instrumentation for AgentForge.
"""
import os
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Dict, Generator, Optional, TypeVar

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.metrics import CallbackOptions, Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

from services.shared.config import settings

T = TypeVar("T")

# Global tracer and meter
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None


def init_telemetry(service_name: Optional[str] = None) -> None:
    """Initialize OpenTelemetry tracing and metrics."""
    global _tracer_provider, _meter_provider
    
    service_name = service_name or settings.OTEL_SERVICE_NAME
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "0.1.0",
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
    })
    
    # Initialize tracing
    _tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(_tracer_provider)
    
    otlp_trace_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=True,
    )
    _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
    
    # Initialize metrics
    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=True,
    )
    metric_reader = PeriodicExportingMetricReader(
        exporter=otlp_metric_exporter,
        export_interval_millis=30000,
    )
    _meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(_meter_provider)
    
    # Auto-instrument libraries
    FastAPIInstrumentor.instrument()
    HTTPXClientInstrumentor.instrument()
    RedisInstrumentor.instrument()
    SQLAlchemyInstrumentor.instrument()


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    """Get a meter instance."""
    return metrics.get_meter(name)


# Common metrics
meter = get_meter("agentforge")

workflow_duration = meter.create_histogram(
    name="workflow.duration",
    description="Workflow execution duration in seconds",
    unit="s",
)

workflow_total = meter.create_counter(
    name="workflow.total",
    description="Total number of workflows",
)

task_duration = meter.create_histogram(
    name="task.duration",
    description="Task execution duration in seconds",
    unit="s",
)

task_total = meter.create_counter(
    name="task.total",
    description="Total number of tasks",
)

agent_duration = meter.create_histogram(
    name="agent.duration",
    description="Agent execution duration in seconds",
    unit="s",
)

agent_total = meter.create_counter(
    name="agent.total",
    description="Total number of agent executions",
)

llm_tokens = meter.create_histogram(
    name="llm.tokens",
    description="LLM token usage",
    unit="tokens",
)

llm_cost = meter.create_histogram(
    name="llm.cost",
    description="LLM cost in USD",
    unit="USD",
)

rag_retrieval_duration = meter.create_histogram(
    name="rag.retrieval.duration",
    description="RAG retrieval duration in seconds",
    unit="s",
)

rag_results_count = meter.create_histogram(
    name="rag.results.count",
    description="Number of RAG results retrieved",
)

memory_operation_duration = meter.create_histogram(
    name="memory.operation.duration",
    description="Memory operation duration in seconds",
    unit="s",
)

deployment_duration = meter.create_histogram(
    name="deployment.duration",
    description="Deployment duration in seconds",
    unit="s",
)

active_workflows = meter.create_up_down_counter(
    name="workflows.active",
    description="Number of active workflows",
)

error_total = meter.create_counter(
    name="errors.total",
    description="Total number of errors",
)


@contextmanager
def trace_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None,
) -> Generator[Span, None, None]:
    """Context manager for creating traced spans."""
    tracer = get_tracer("agentforge")
    with tracer.start_as_current_span(name, kind=kind, attributes=attributes or {}) as span:
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def traced(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for tracing function execution."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        span_name = name or f"{func.__module__}.{func.__qualname__}"
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            with trace_span(span_name, kind, attributes) as span:
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            with trace_span(span_name, kind, attributes) as span:
                return await func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper
    
    return decorator


def record_workflow_metrics(
    workflow_id: str,
    duration: float,
    status: str,
    phase: str,
    tokens: int = 0,
    cost: float = 0.0,
) -> None:
    """Record workflow execution metrics."""
    workflow_duration.record(duration, {"workflow_id": workflow_id, "phase": phase, "status": status})
    workflow_total.add(1, {"workflow_id": workflow_id, "phase": phase, "status": status})
    if tokens > 0:
        llm_tokens.record(tokens, {"workflow_id": workflow_id})
    if cost > 0:
        llm_cost.record(cost, {"workflow_id": workflow_id})


def record_task_metrics(
    task_id: str,
    agent_role: str,
    duration: float,
    status: str,
) -> None:
    """Record task execution metrics."""
    task_duration.record(duration, {"task_id": task_id, "agent_role": agent_role, "status": status})
    task_total.add(1, {"task_id": task_id, "agent_role": agent_role, "status": status})


def record_agent_metrics(
    agent_role: str,
    duration: float,
    status: str,
    tokens: int = 0,
    cost: float = 0.0,
) -> None:
    """Record agent execution metrics."""
    agent_duration.record(duration, {"agent_role": agent_role, "status": status})
    agent_total.add(1, {"agent_role": agent_role, "status": status})
    if tokens > 0:
        llm_tokens.record(tokens, {"agent_role": agent_role})
    if cost > 0:
        llm_cost.record(cost, {"agent_role": agent_role})


def record_rag_metrics(
    query: str,
    duration: float,
    results_count: int,
    source: str,
) -> None:
    """Record RAG retrieval metrics."""
    rag_retrieval_duration.record(duration, {"source": source})
    rag_results_count.record(results_count, {"source": source})


def record_memory_metrics(
    memory_type: str,
    operation: str,
    duration: float,
    success: bool,
) -> None:
    """Record memory operation metrics."""
    memory_operation_duration.record(
        duration,
        {"memory_type": memory_type, "operation": operation, "success": str(success).lower()},
    )


def record_error(error_type: str, component: str) -> None:
    """Record error metrics."""
    error_total.add(1, {"error_type": error_type, "component": component})


def shutdown_telemetry() -> None:
    """Shutdown telemetry providers."""
    global _tracer_provider, _meter_provider
    if _tracer_provider:
        _tracer_provider.shutdown()
    if _meter_provider:
        _meter_provider.shutdown()
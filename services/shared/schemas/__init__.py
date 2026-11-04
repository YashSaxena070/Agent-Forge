"""
Shared Pydantic schemas for AgentForge inter-service communication.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator
from pydantic.config import ConfigDict


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    APPROVAL_REQUIRED = "approval_required"
    WAITING_DEPENDENCY = "waiting_dependency"


class AgentRole(str, Enum):
    """Specialized agent roles."""
    PLANNER = "planner"
    PRODUCT_MANAGER = "product_manager"
    ARCHITECT = "architect"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATABASE = "database"
    QA = "qa"
    SECURITY = "security"
    DEVOPS = "devops"
    REVIEWER = "reviewer"


class WorkflowPhase(str, Enum):
    """Workflow execution phases."""
    PLANNING = "planning"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ArtifactType(str, Enum):
    """Types of artifacts produced by agents."""
    CODE = "code"
    DOCUMENT = "document"
    DIAGRAM = "diagram"
    TEST = "test"
    CONFIG = "config"
    SPEC = "spec"
    REPORT = "report"
    DEPLOYMENT_MANIFEST = "deployment_manifest"


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        json_schema_extra={"examples": []},
    )


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IDMixin(BaseModel):
    """Mixin for UUID identification."""
    id: UUID = Field(default_factory=uuid4)


class TaskBase(BaseSchema):
    """Base task schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    role: AgentRole
    priority: Priority = Field(default=Priority.MEDIUM)
    dependencies: List[UUID] = Field(default_factory=list)
    estimated_effort: Optional[str] = Field(default=None, description="e.g., '2h', '1d', '3d'")
    tags: List[str] = Field(default_factory=list)


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    project_id: UUID
    workflow_id: Optional[UUID] = None


class TaskUpdate(BaseSchema):
    """Schema for updating a task."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    assignee_id: Optional[UUID] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Task(TaskBase, IDMixin, TimestampMixin):
    """Complete task schema."""
    project_id: UUID
    workflow_id: Optional[UUID] = None
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    assignee_id: Optional[UUID] = None
    progress: int = Field(default=0, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    artifacts: List["Artifact"] = Field(default_factory=list)


class ArtifactBase(BaseSchema):
    """Base artifact schema."""
    name: str = Field(..., min_length=1, max_length=255)
    type: ArtifactType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None


class ArtifactCreate(ArtifactBase):
    """Schema for creating an artifact."""
    task_id: UUID
    project_id: UUID
    created_by: UUID


class Artifact(ArtifactBase, IDMixin, TimestampMixin):
    """Complete artifact schema."""
    task_id: UUID
    project_id: UUID
    created_by: UUID
    version: int = Field(default=1)
    parent_id: Optional[UUID] = None


class ProjectBase(BaseSchema):
    """Base project schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    repository_url: Optional[str] = None
    technology_stack: List[str] = Field(default_factory=list)
    requirements: Dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    owner_id: UUID


class ProjectUpdate(BaseSchema):
    """Schema for updating a project."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = None
    repository_url: Optional[str] = None
    technology_stack: Optional[List[str]] = None
    requirements: Optional[Dict[str, Any]] = None


class Project(ProjectBase, IDMixin, TimestampMixin):
    """Complete project schema."""
    owner_id: UUID
    status: str = Field(default="active")
    settings: Dict[str, Any] = Field(default_factory=dict)


class WorkflowBase(BaseSchema):
    """Base workflow schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: str
    project_id: UUID
    initial_state: Dict[str, Any] = Field(default_factory=dict)


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow."""
    pass


class WorkflowUpdate(BaseSchema):
    """Schema for updating a workflow."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[WorkflowPhase] = None


class Workflow(WorkflowBase, IDMixin, TimestampMixin):
    """Complete workflow schema."""
    status: str = Field(default="created")
    current_phase: WorkflowPhase = Field(default=WorkflowPhase.PLANNING)
    progress: int = Field(default=0, ge=0, le=100)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    state: Dict[str, Any] = Field(default_factory=dict)
    tasks: List[Task] = Field(default_factory=list)


class AgentMessageBase(BaseSchema):
    """Base agent message schema for inter-agent communication."""
    task_id: UUID
    from_agent: AgentRole
    to_agent: AgentRole
    message_type: str = Field(..., description="Type of message: request, response, notification")
    payload: Dict[str, Any]
    correlation_id: Optional[UUID] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_approval: bool = False


class AgentMessage(AgentMessageBase, IDMixin, TimestampMixin):
    """Complete agent message schema."""
    status: str = Field(default="sent")
    acknowledged_at: Optional[datetime] = None
    response_id: Optional[UUID] = None


class ApprovalRequest(BaseSchema):
    """Schema for human-in-the-loop approval requests."""
    workflow_id: UUID
    task_id: UUID
    title: str
    description: str
    options: List[Dict[str, Any]] = Field(default_factory=list)
    requested_by: AgentRole
    expires_at: Optional[datetime] = None


class ApprovalResponse(BaseSchema):
    """Schema for approval responses."""
    request_id: UUID
    approved: bool
    selected_option: Optional[str] = None
    comments: Optional[str] = None
    decided_by: UUID


class DeploymentBase(BaseSchema):
    """Base deployment schema."""
    project_id: UUID
    workflow_id: UUID
    environment: str = Field(..., description="target environment: dev, staging, prod")
    strategy: str = Field(default="rolling", description="deployment strategy")
    config: Dict[str, Any] = Field(default_factory=dict)


class DeploymentCreate(DeploymentBase):
    """Schema for creating a deployment."""
    triggered_by: UUID


class Deployment(DeploymentBase, IDMixin, TimestampMixin):
    """Complete deployment schema."""
    triggered_by: UUID
    status: str = Field(default="pending")
    version: str
    artifacts: List[Artifact] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    rollback_version: Optional[str] = None


class MetricPoint(BaseSchema):
    """Single metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = Field(default_factory=dict)


class WorkflowMetrics(BaseSchema):
    """Aggregated workflow metrics."""
    workflow_id: UUID
    duration_seconds: Optional[float] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    agent_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    phase_durations: Dict[str, float] = Field(default_factory=dict)


class HealthCheck(BaseSchema):
    """Health check response."""
    status: str = Field(..., description="healthy, degraded, unhealthy")
    service: str
    version: str
    checks: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Forward references resolution
Task.model_rebuild()
Artifact.model_rebuild()
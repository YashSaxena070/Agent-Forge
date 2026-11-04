"""
Database entity models.
"""
import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    Integer,
    Boolean,
    Float,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.backend.src.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    OPERATOR = "operator"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class WorkflowStatus(str, enum.Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowPhase(str, enum.Enum):
    PLANNING = "planning"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    APPROVAL_REQUIRED = "approval_required"
    WAITING_DEPENDENCY = "waiting_dependency"


class AgentRole(str, enum.Enum):
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


class ArtifactType(str, enum.Enum):
    CODE = "code"
    DOCUMENT = "document"
    DIAGRAM = "diagram"
    TEST = "test"
    CONFIG = "config"
    SPEC = "spec"
    REPORT = "report"
    DEPLOYMENT_MANIFEST = "deployment_manifest"


class DeploymentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentStrategy(str, enum.Enum):
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.DEVELOPER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="owner")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="assignee")
    approvals: Mapped[list["ApprovalRequest"]] = relationship("ApprovalRequest", back_populates="decided_by_user")
    deployments: Mapped[list["Deployment"]] = relationship("Deployment", back_populates="triggered_by_user")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="created_by_user")
    mfa_methods: Mapped[list["MFAMethod"]] = relationship("MFAMethod", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    login_attempts: Mapped[list["LoginAttempt"]] = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    """Project model."""
    __tablename__ = "projects"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    repository_url: Mapped[str] = mapped_column(String(500), nullable=True)
    technology_stack: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    requirements: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    owner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    workflows: Mapped[list["Workflow"]] = relationship("Workflow", back_populates="project")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="project")
    deployments: Mapped[list["Deployment"]] = relationship("Deployment", back_populates="project")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="project")
    
    __table_args__ = (
        Index("ix_projects_owner_created", "owner_id", "created_at"),
    )


class Workflow(Base):
    """Workflow model."""
    __tablename__ = "workflows"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[WorkflowStatus] = mapped_column(Enum(WorkflowStatus), default=WorkflowStatus.CREATED, nullable=False)
    current_phase: Mapped[WorkflowPhase] = mapped_column(Enum(WorkflowPhase), default=WorkflowPhase.PLANNING, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    initial_state: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    state: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error: Mapped[str] = mapped_column(Text, nullable=True)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="workflows")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="workflow")
    approvals: Mapped[list["ApprovalRequest"]] = relationship("ApprovalRequest", back_populates="workflow")
    deployments: Mapped[list["Deployment"]] = relationship("Deployment", back_populates="workflow")
    
    __table_args__ = (
        Index("ix_workflows_project_status", "project_id", "status"),
    )


class Task(Base):
    """Task model."""
    __tablename__ = "tasks"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[AgentRole] = mapped_column(Enum(AgentRole), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    dependencies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    estimated_effort: Mapped[str] = mapped_column(String(50), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    assignee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error: Mapped[str] = mapped_column(Text, nullable=True)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    workflow_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflows.id"), nullable=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="tasks")
    assignee: Mapped["User"] = relationship("User", back_populates="tasks")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="task")
    agent_executions: Mapped[list["AgentExecution"]] = relationship("AgentExecution", back_populates="task")
    
    __table_args__ = (
        Index("ix_tasks_workflow_status", "workflow_id", "status"),
        Index("ix_tasks_project_role", "project_id", "role"),
    )


class Artifact(Base):
    """Artifact model."""
    __tablename__ = "artifacts"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    task_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    created_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parent_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("artifacts.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="artifacts")
    project: Mapped["Project"] = relationship("Project", back_populates="artifacts")
    created_by_user: Mapped["User"] = relationship("User", back_populates="artifacts")
    parent: Mapped["Artifact"] = relationship("Artifact", remote_side=[id], backref="children")


class Deployment(Base):
    """Deployment model."""
    __tablename__ = "deployments"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    environment: Mapped[str] = mapped_column(String(50), nullable=False)
    strategy: Mapped[DeploymentStrategy] = mapped_column(Enum(DeploymentStrategy), default=DeploymentStrategy.ROLLING, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[DeploymentStatus] = mapped_column(Enum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    logs: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    error: Mapped[str] = mapped_column(Text, nullable=True)
    rollback_version: Mapped[str] = mapped_column(String(100), nullable=True)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    workflow_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
    triggered_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="deployments")
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="deployments")
    triggered_by_user: Mapped["User"] = relationship("User", back_populates="deployments")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", secondary="deployment_artifacts", backref="deployments")


class ApprovalRequest(Base):
    """Approval request model for human-in-the-loop."""
    __tablename__ = "approval_requests"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(50), nullable=False)
    decided_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    selected_option: Mapped[str] = mapped_column(String(100), nullable=True)
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    workflow_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True)
    task_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="approvals")
    decided_by_user: Mapped["User"] = relationship("User", back_populates="approvals")


class AgentExecution(Base):
    """Agent execution tracking."""
    __tablename__ = "agent_executions"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_role: Mapped[AgentRole] = mapped_column(Enum(AgentRole), nullable=False, index=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    input_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    output_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error: Mapped[str] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    task_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="agent_executions")


class LongTermMemory(Base):
    """Long-term persistent memory for projects."""
    __tablename__ = "long_term_memory"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project")
    
    __table_args__ = (
        UniqueConstraint("project_id", "key", name="uq_ltm_project_key"),
    )


# Association table for deployment artifacts
from sqlalchemy import Table

deployment_artifacts = Table(
    "deployment_artifacts",
    Base.metadata,
    Column("deployment_id", PGUUID(as_uuid=True), ForeignKey("deployments.id"), primary_key=True),
    Column("artifact_id", PGUUID(as_uuid=True), ForeignKey("artifacts.id"), primary_key=True),
)

from sqlalchemy import Column

# Import MFA models
from apps.backend.src.models.entities.mfa import (
    MFAMethod,
    MFAType,
    MFAStatus,
    UserSession,
    LoginAttempt,
)

# Import multitenancy models
from apps.backend.src.models.entities.multitenancy import (
    Organization,
    Workspace,
    OrganizationMember,
    WorkspaceMember,
    WorkspaceInvitation,
    BillingEvent,
    ApiKey,
    WorkspaceStatus,
    WorkspacePlan,
    MemberRole,
)

# Import disaster recovery models
from apps.backend.src.models.entities.disaster_recovery import (
    BackupRecord,
    RestoreRecord,
    BackupType,
    BackupStatus,
    RestoreStatus,
    StorageBackend,
)
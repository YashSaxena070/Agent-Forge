"""
Multi-tenancy workspace and organization models.
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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.backend.src.core.database import Base


class WorkspaceStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    TRIAL = "trial"


class WorkspacePlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    OPERATOR = "operator"
    SECURITY = "security"
    BILLING = "billing"


class Organization(Base):
    """Organization/tenant root entity."""
    __tablename__ = "organizations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Branding
    logo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(7), nullable=True)  # Hex color
    
    # Settings
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Compliance
    data_residency: Mapped[str] = mapped_column(String(100), nullable=True)  # e.g., "us-east-1", "eu-west-1"
    compliance_frameworks: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # ["SOC2", "HIPAA", "GDPR"]
    
    # Status
    status: Mapped[WorkspaceStatus] = mapped_column(Enum(WorkspaceStatus), default=WorkspaceStatus.ACTIVE, nullable=False)
    plan: Mapped[WorkspacePlan] = mapped_column(Enum(WorkspacePlan), default=WorkspacePlan.FREE, nullable=False)
    
    # Billing
    billing_email: Mapped[str] = mapped_column(String(255), nullable=True)
    billing_address: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    subscription_id: Mapped[str] = mapped_column(String(255), nullable=True)
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Limits
    max_workspaces: Mapped[int] = mapped_column(Integer, default=10)
    max_users: Mapped[int] = mapped_column(Integer, default=100)
    max_projects_per_workspace: Mapped[int] = mapped_column(Integer, default=50)
    max_api_calls_per_month: Mapped[int] = mapped_column(Integer, default=1000000)
    storage_limit_gb: Mapped[int] = mapped_column(Integer, default=10)
    
    # Security
    enforce_mfa: Mapped[bool] = mapped_column(Boolean, default=False)
    session_timeout_minutes: Mapped[int] = mapped_column(Integer, default=480)
    allowed_ip_ranges: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    saml_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    oidc_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspaces: Mapped[list["Workspace"]] = relationship("Workspace", back_populates="organization", cascade="all, delete-orphan")
    members: Mapped[list["OrganizationMember"]] = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    billing_events: Mapped[list["BillingEvent"]] = relationship("BillingEvent", back_populates="organization", cascade="all, delete-orphan")


class Workspace(Base):
    """Workspace within an organization (project container)."""
    __tablename__ = "workspaces"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Organization
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Settings
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Visibility
    visibility: Mapped[str] = mapped_column(String(50), default="private", nullable=False)  # private, organization, public
    
    # Defaults for projects
    default_project_settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    default_tech_stack: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Resource quotas
    max_projects: Mapped[int] = mapped_column(Integer, default=50)
    max_concurrent_workflows: Mapped[int] = mapped_column(Integer, default=10)
    storage_limit_gb: Mapped[int] = mapped_column(Integer, default=5)
    
    # Status
    status: Mapped[WorkspaceStatus] = mapped_column(Enum(WorkspaceStatus), default=WorkspaceStatus.ACTIVE, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="workspaces")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")
    members: Mapped[list["WorkspaceMember"]] = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    invitations: Mapped[list["WorkspaceInvitation"]] = relationship("WorkspaceInvitation", back_populates="workspace", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_workspace_org_slug"),
        Index("ix_workspaces_org_status", "organization_id", "status"),
    )


class OrganizationMember(Base):
    """Organization-level membership."""
    __tablename__ = "organization_members"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.DEVELOPER, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # active, pending, suspended
    
    # Permissions override
    custom_permissions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    invited_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="members")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    inviter: Mapped["User"] = relationship("User", foreign_keys=[invited_by])
    
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
        Index("ix_org_members_user_status", "user_id", "status"),
    )


class WorkspaceMember(Base):
    """Workspace-level membership."""
    __tablename__ = "workspace_members"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.DEVELOPER, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    
    # Permissions
    custom_permissions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    invited_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="members")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    inviter: Mapped["User"] = relationship("User", foreign_keys=[invited_by])
    
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        Index("ix_ws_members_user_status", "user_id", "status"),
    )


class WorkspaceInvitation(Base):
    """Workspace invitation for new members."""
    __tablename__ = "workspace_invitations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole), default=MemberRole.DEVELOPER, nullable=False)
    
    # Token
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, accepted, expired, revoked
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Inviter
    invited_by: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="invitations")
    inviter: Mapped["User"] = relationship("User", foreign_keys=[invited_by])
    acceptor: Mapped["User"] = relationship("User", foreign_keys=[accepted_by])
    
    __table_args__ = (
        Index("ix_ws_invitations_email_status", "email", "status"),
    )


class BillingEvent(Base):
    """Billing event tracking."""
    __tablename__ = "billing_events"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # subscription_created, invoice_paid, usage_recorded, etc.
    amount_usd: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    
    # Provider
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # stripe, paddle, manual
    provider_event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=True, index=True)
    
    # Details
    description: Mapped[str] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, completed, failed, refunded
    
    # Timestamps
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="billing_events")
    
    __table_args__ = (
        Index("ix_billing_events_org_time", "organization_id", "occurred_at"),
    )


class ApiKey(Base):
    """API keys for programmatic access."""
    __tablename__ = "api_keys"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True, index=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)  # af_live_, af_test_
    hashed_key: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Permissions
    scopes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Rate limits
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=100)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, default=1000)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_rotated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization")
    workspace: Mapped["Workspace"] = relationship("Workspace")
    owner: Mapped["User"] = relationship("User")
    
    __table_args__ = (
        Index("ix_api_keys_user_active", "user_id", "is_active"),
        Index("ix_api_keys_expires", "expires_at"),
    )
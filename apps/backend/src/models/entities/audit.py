"""
Audit Log Database Model
"""
import hashlib
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
    select,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.backend.src.core.audit import AuditEventType, AuditSeverity
from apps.backend.src.core.database import Base


class AuditLog(Base):
    """Immutable audit log entry."""
    __tablename__ = "audit_logs"
    
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(Enum(AuditEventType), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(Enum(AuditSeverity), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Actor
    actor_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    actor_user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Resource
    resource_type: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    resource_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    resource_name: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Action
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Context
    request_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    correlation_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    
    # Details
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Risk
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_factors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Compliance
    compliance_tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    data_classification: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Cryptographic integrity
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    
    # Relationships
    actor: Mapped["User"] = relationship("User")
    
    __table_args__ = (
        Index("ix_audit_logs_timestamp_type", "timestamp", "event_type"),
        Index("ix_audit_logs_actor_time", "actor_id", "timestamp"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_compliance", "compliance_tags", postgresql_using="gin"),
    )
    
    def __setattr__(self, name, value):
        # Make immutable after creation
        if name == "event_hash" and hasattr(self, "event_hash") and self.event_hash:
            raise AttributeError("Audit log is immutable")
        super().__setattr__(name, value)
    
    @classmethod
    async def verify_chain(cls, start_time: datetime, end_time: datetime) -> bool:
        """Verify hash chain integrity for time range."""
        from apps.backend.src.core.database import db_manager
        
        async with db_manager.session() as session:
            result = await session.execute(
                select(cls)
                .where(cls.timestamp >= start_time)
                .where(cls.timestamp <= end_time)
                .order_by(cls.timestamp.asc())
            )
            logs = result.scalars().all()
            
            previous_hash = None
            for log in logs:
                # Recompute hash
                event_data = {
                    "event_id": str(log.event_id),
                    "event_type": log.event_type,
                    "timestamp": log.timestamp.isoformat(),
                    "actor_id": str(log.actor_id) if log.actor_id else None,
                    "action": log.action,
                    "outcome": log.outcome,
                    "details": log.details,
                    "previous_hash": log.previous_hash,
                }
                serialized = json.dumps(event_data, sort_keys=True, separators=(",", ":"))
                computed_hash = hashlib.sha256(serialized.encode()).hexdigest()
                
                if computed_hash != log.event_hash:
                    return False
                
                if log.previous_hash != previous_hash:
                    return False
                
                previous_hash = log.event_hash
            
            return True


import json
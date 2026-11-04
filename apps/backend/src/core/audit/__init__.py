"""
Immutable Audit Logging with Compliance Support
"""
import hashlib
import json
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.core.database import db_manager
from apps.backend.src.core.config import settings
from apps.backend.src.core.tools import get_tool_executor


class AuditEventType(str, Enum):
    """Types of auditable events."""
    # Authentication
    LOGIN_SUCCESS = "login.success"
    LOGIN_FAILURE = "login.failure"
    LOGOUT = "logout"
    MFA_ENABLED = "mfa.enabled"
    MFA_DISABLED = "mfa.disabled"
    MFA_VERIFIED = "mfa.verified"
    
    # Authorization
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_DENIED = "permission.denied"
    ROLE_ASSIGNED = "role.assigned"
    ROLE_REVOKED = "role.revoked"
    
    # Resource Management
    RESOURCE_CREATED = "resource.created"
    RESOURCE_READ = "resource.read"
    RESOURCE_UPDATED = "resource.updated"
    RESOURCE_DELETED = "resource.deleted"
    RESOURCE_EXPORTED = "resource.exported"
    
    # Project/Workflow
    PROJECT_CREATED = "project.created"
    PROJECT_DELETED = "project.deleted"
    WORKFLOW_EXECUTED = "workflow.executed"
    WORKFLOW_APPROVED = "workflow.approved"
    DEPLOYMENT_STARTED = "deployment.started"
    DEPLOYMENT_COMPLETED = "deployment.completed"
    DEPLOYMENT_ROLLED_BACK = "deployment.rolled_back"
    
    # Security
    SECRET_ACCESSED = "secret.accessed"
    SECRET_ROTATED = "secret.rotated"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    BRUTE_FORCE_DETECTED = "security.brute_force"
    
    # Compliance
    DATA_EXPORT = "compliance.data_export"
    DATA_ACCESS = "compliance.data_access"
    RETENTION_POLICY_APPLIED = "compliance.retention_applied"
    
    # System
    CONFIG_CHANGED = "system.config_changed"
    BACKUP_CREATED = "system.backup_created"
    RESTORE_INITIATED = "system.restore_initiated"


class AuditSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Immutable audit event."""
    event_id: UUID = field(default_factory=uuid4)
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Actor
    actor_id: Optional[UUID] = None
    actor_type: str = "user"  # user, system, agent
    actor_ip: Optional[str] = None
    actor_user_agent: Optional[str] = None
    
    # Resource
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    resource_name: Optional[str] = None
    
    # Action
    action: str = ""
    outcome: str = "success"  # success, failure, partial
    
    # Context
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # Details (structured, no PII in production)
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Risk
    risk_score: int = 0  # 0-100
    risk_factors: List[str] = field(default_factory=list)
    
    # Compliance
    compliance_tags: List[str] = field(default_factory=list)
    data_classification: Optional[str] = None
    
    # Cryptographic integrity
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None
    
    def compute_hash(self) -> str:
        """Compute cryptographic hash of event."""
        # Create deterministic representation
        data = {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "action": self.action,
            "outcome": self.outcome,
            "details": self.details,
            "previous_hash": self.previous_hash,
        }
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode()).hexdigest()


class AuditLogger:
    """Immutable audit logger with tamper-evident chain."""
    
    def __init__(self):
        self._buffer: List[AuditEvent] = []
        self._buffer_size = 100
        self._flush_interval = 5  # seconds
        self._last_hash: Optional[str] = None
        self._running = False
    
    async def log(
        self,
        event_type: AuditEventType,
        action: str,
        actor_id: Optional[UUID] = None,
        actor_type: str = "user",
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        resource_name: Optional[str] = None,
        outcome: str = "success",
        severity: AuditSeverity = AuditSeverity.LOW,
        details: Dict[str, Any] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        actor_ip: Optional[str] = None,
        actor_user_agent: Optional[str] = None,
        risk_score: int = 0,
        risk_factors: List[str] = None,
        compliance_tags: List[str] = None,
        data_classification: Optional[str] = None,
    ) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_ip=actor_ip,
            actor_user_agent=actor_user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            action=action,
            outcome=outcome,
            request_id=request_id,
            session_id=session_id,
            correlation_id=correlation_id,
            details=details or {},
            risk_score=risk_score,
            risk_factors=risk_factors or [],
            compliance_tags=compliance_tags or [],
            data_classification=data_classification,
            previous_hash=self._last_hash,
        )
        
        # Compute hash for integrity chain
        event.event_hash = event.compute_hash()
        self._last_hash = event.event_hash
        
        # Add to buffer
        self._buffer.append(event)
        
        # Flush if buffer full
        if len(self._buffer) >= self._buffer_size:
            await self.flush()
        
        return event
    
    async def flush(self):
        """Flush buffer to persistent storage."""
        if not self._buffer:
            return
        
        events = self._buffer[:]
        self._buffer.clear()
        
        # Store in database
        async with db_manager.session() as session:
            from apps.backend.src.models.entities.audit import AuditLog
            
            for event in events:
                log = AuditLog(
                    event_id=event.event_id,
                    event_type=event.event_type.value,
                    severity=event.severity.value,
                    timestamp=event.timestamp,
                    actor_id=event.actor_id,
                    actor_type=event.actor_type,
                    actor_ip=event.actor_ip,
                    actor_user_agent=event.actor_user_agent,
                    resource_type=event.resource_type,
                    resource_id=event.resource_id,
                    resource_name=event.resource_name,
                    action=event.action,
                    outcome=event.outcome,
                    request_id=event.request_id,
                    session_id=event.session_id,
                    correlation_id=event.correlation_id,
                    details=event.details,
                    risk_score=event.risk_score,
                    risk_factors=event.risk_factors,
                    compliance_tags=event.compliance_tags,
                    data_classification=event.data_classification,
                    previous_hash=event.previous_hash,
                    event_hash=event.event_hash,
                )
                session.add(log)
            
            await session.commit()
        
        # Also write to immutable log file (WORM storage)
        await self._write_to_immutable_log(events)
    
    async def _write_to_immutable_log(self, events: List[AuditEvent]):
        """Write to append-only log file (simulated WORM)."""
        import os
        log_dir = "/var/log/agentforge/audit"
        os.makedirs(log_dir, exist_ok=True)
        
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = os.path.join(log_dir, f"audit-{date_str}.log")
        
        lines = []
        for event in events:
            lines.append(json.dumps({
                "event_id": str(event.event_id),
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "actor_id": str(event.actor_id) if event.actor_id else None,
                "action": event.action,
                "outcome": event.outcome,
                "resource_type": event.resource_type,
                "resource_id": str(event.resource_id) if event.resource_id else None,
                "severity": event.severity.value,
                "details": event.details,
                "event_hash": event.event_hash,
                "previous_hash": event.previous_hash,
            }, separators=(",", ":")))
        
        # In production, this would write to WORM storage (S3 Object Lock, etc.)
        with open(log_file, "a") as f:
            f.write("\n".join(lines) + "\n")
    
    async def start_background_flush(self):
        """Start background flush task."""
        self._running = True
        while self._running:
            await asyncio.sleep(self._flush_interval)
            if self._buffer:
                await self.flush()
    
    def stop_background_flush(self):
        self._running = False


class AuditLog(BaseModel):
    """Audit log entry for storage."""
    event_id: UUID
    event_type: str
    severity: str
    timestamp: datetime
    actor_id: Optional[UUID] = None
    actor_type: str
    actor_ip: Optional[str] = None
    actor_user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    resource_name: Optional[str] = None
    action: str
    outcome: str
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    risk_score: int = 0
    risk_factors: List[str] = Field(default_factory=list)
    compliance_tags: List[str] = Field(default_factory=list)
    data_classification: Optional[str] = None
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None


class AuditQuery(BaseModel):
    """Query parameters for audit log search."""
    event_types: List[AuditEventType] = Field(default_factory=list)
    actor_ids: List[UUID] = Field(default_factory=list)
    resource_types: List[str] = Field(default_factory=list)
    resource_ids: List[UUID] = Field(default_factory=list)
    outcomes: List[str] = Field(default_factory=list)
    severities: List[AuditSeverity] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    compliance_tags: List[str] = Field(default_factory=list)
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class ComplianceReport(BaseModel):
    """Compliance audit report."""
    report_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    period_start: datetime
    period_end: datetime
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    events_by_outcome: Dict[str, int]
    failed_logins: int
    permission_denials: int
    data_access_events: int
    admin_actions: int
    suspicious_activities: int
    integrity_verified: bool
    hash_chain_verified: bool


class AuditService:
    """Service for audit log management and compliance reporting."""
    
    def __init__(self, logger: AuditLogger = None):
        self.logger = logger or AuditLogger()
    
    async def initialize(self):
        """Initialize audit service."""
        await self.logger.start_background_flush()
    
    async def shutdown(self):
        """Shutdown audit service."""
        self.logger.stop_background_flush()
        await self.logger.flush()
    
    @asynccontextmanager
    async def audit_context(
        self,
        event_type: AuditEventType,
        action: str,
        actor_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        **kwargs,
    ):
        """Context manager for automatic audit logging."""
        start_time = datetime.now(timezone.utc)
        outcome = "success"
        error = None
        
        try:
            yield
        except Exception as e:
            outcome = "failure"
            error = str(e)
            raise
        finally:
            details = {
                "duration_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
            }
            if error:
                details["error"] = error
            
            await self.logger.log(
                event_type=event_type,
                action=action,
                actor_id=actor_id,
                resource_type=resource_type,
                resource_id=resource_id,
                outcome=outcome,
                details=details,
                **kwargs,
            )
    
    async def log_event(self, **kwargs) -> AuditEvent:
        """Log a single event."""
        return await self.logger.log(**kwargs)
    
    async def query_logs(self, query: AuditQuery) -> List[AuditLog]:
        """Query audit logs."""
        async with db_manager.session() as session:
            from apps.backend.src.models.entities.audit import AuditLog as AuditLogModel
            
            stmt = select(AuditLogModel)
            
            if query.event_types:
                stmt = stmt.where(AuditLogModel.event_type.in_([e.value for e in query.event_types]))
            
            if query.actor_ids:
                stmt = stmt.where(AuditLogModel.actor_id.in_(query.actor_ids))
            
            if query.resource_types:
                stmt = stmt.where(AuditLogModel.resource_type.in_(query.resource_types))
            
            if query.resource_ids:
                stmt = stmt.where(AuditLogModel.resource_id.in_(query.resource_ids))
            
            if query.outcomes:
                stmt = stmt.where(AuditLogModel.outcome.in_(query.outcomes))
            
            if query.severities:
                stmt = stmt.where(AuditLogModel.severity.in_([s.value for s in query.severities]))
            
            if query.start_time:
                stmt = stmt.where(AuditLogModel.timestamp >= query.start_time)
            
            if query.end_time:
                stmt = stmt.where(AuditLogModel.timestamp <= query.end_time)
            
            if query.compliance_tags:
                stmt = stmt.where(
                    AuditLogModel.compliance_tags.op("@>")(query.compliance_tags)
                )
            
            stmt = stmt.order_by(AuditLogModel.timestamp.desc())
            stmt = stmt.offset(query.offset).limit(query.limit)
            
            result = await session.execute(stmt)
            logs = result.scalars().all()
            
            return [
                AuditLog(
                    event_id=log.event_id,
                    event_type=log.event_type,
                    severity=log.severity,
                    timestamp=log.timestamp,
                    actor_id=log.actor_id,
                    actor_type=log.actor_type,
                    actor_ip=log.actor_ip,
                    actor_user_agent=log.actor_user_agent,
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    resource_name=log.resource_name,
                    action=log.action,
                    outcome=log.outcome,
                    request_id=log.request_id,
                    session_id=log.session_id,
                    correlation_id=log.correlation_id,
                    details=log.details,
                    risk_score=log.risk_score,
                    risk_factors=log.risk_factors,
                    compliance_tags=log.compliance_tags,
                    data_classification=log.data_classification,
                    previous_hash=log.previous_hash,
                    event_hash=log.event_hash,
                )
                for log in logs
            ]
    
    async def generate_compliance_report(
        self,
        period_start: datetime,
        period_end: datetime,
    ) -> ComplianceReport:
        """Generate compliance audit report."""
        query = AuditQuery(
            start_time=period_start,
            end_time=period_end,
            limit=10000,
        )
        
        logs = await self.query_logs(query)
        
        # Verify hash chain integrity
        integrity_verified = await self._verify_hash_chain(period_start, period_end)
        
        # Aggregate statistics
        events_by_type = {}
        events_by_severity = {}
        events_by_outcome = {}
        failed_logins = 0
        permission_denials = 0
        data_access_events = 0
        admin_actions = 0
        suspicious_activities = 0
        
        for log in logs:
            events_by_type[log.event_type] = events_by_type.get(log.event_type, 0) + 1
            events_by_severity[log.severity] = events_by_severity.get(log.severity, 0) + 1
            events_by_outcome[log.outcome] = events_by_outcome.get(log.outcome, 0) + 1
            
            if log.event_type == "login.failure":
                failed_logins += 1
            elif log.event_type == "permission.denied":
                permission_denials += 1
            elif log.event_type in ["resource.read", "data.exported", "compliance.data_access"]:
                data_access_events += 1
            elif log.actor_type == "admin" or "admin" in log.details.get("roles", []):
                admin_actions += 1
            elif log.event_type == "security.suspicious_activity":
                suspicious_activities += 1
        
        return ComplianceReport(
            period_start=period_start,
            period_end=period_end,
            total_events=len(logs),
            events_by_type=events_by_type,
            events_by_severity=events_by_severity,
            events_by_outcome=events_by_outcome,
            failed_logins=failed_logins,
            permission_denials=permission_denials,
            data_access_events=data_access_events,
            admin_actions=admin_actions,
            suspicious_activities=suspicious_activities,
            integrity_verified=integrity_verified,
            hash_chain_verified=integrity_verified,
        )
    
    async def _verify_hash_chain(self, start: datetime, end: datetime) -> bool:
        """Verify cryptographic hash chain integrity."""
        async with db_manager.session() as session:
            from apps.backend.src.models.entities.audit import AuditLog as AuditLogModel
            
            result = await session.execute(
                select(AuditLogModel)
                .where(AuditLogModel.timestamp >= start)
                .where(AuditLogModel.timestamp <= end)
                .order_by(AuditLogModel.timestamp.asc())
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
    
    async def export_logs(
        self,
        query: AuditQuery,
        format: str = "jsonl",
    ) -> str:
        """Export audit logs for compliance."""
        logs = await self.query_logs(query)
        
        if format == "jsonl":
            lines = [log.model_dump_json() for log in logs]
            return "\n".join(lines)
        elif format == "csv":
            import csv
            import io
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].model_fields.keys())
                writer.writeheader()
                for log in logs:
                    writer.writerow(log.model_dump())
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global audit service
audit_logger = AuditLogger()
audit_service = AuditService(audit_logger)


async def audit_log(
    event_type: AuditEventType,
    action: str,
    actor_id: Optional[UUID] = None,
    **kwargs,
) -> AuditEvent:
    """Convenience function for audit logging."""
    return await audit_service.log_event(
        event_type=event_type,
        action=action,
        actor_id=actor_id,
        **kwargs,
    )
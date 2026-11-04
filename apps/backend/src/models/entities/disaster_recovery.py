"""
Disaster Recovery Models
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
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.backend.src.core.database import Base
from apps.backend.src.core.disaster_recovery import BackupType, BackupStatus, RestoreStatus, StorageBackend


class BackupRecord(Base):
    """Backup execution record."""
    __tablename__ = "backup_records"
    
    backup_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    config_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    backup_type: Mapped[BackupType] = mapped_column(Enum(BackupType), nullable=False)
    status: Mapped[BackupStatus] = mapped_column(Enum(BackupStatus), default=BackupStatus.PENDING, nullable=False, index=True)
    
    # Storage
    storage_backend: Mapped[StorageBackend] = mapped_column(Enum(StorageBackend), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    compressed_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    checksum: Mapped[str] = mapped_column(String(64), nullable=True)
    
    # Metadata
    tables_included: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    row_counts: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Error info
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Retention
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    tags: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("ix_backup_records_config_status", "config_name", "status"),
        Index("ix_backup_records_expires", "expires_at"),
    )


class RestoreRecord(Base):
    """Restore execution record."""
    __tablename__ = "restore_records"
    
    restore_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    backup_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("backup_records.backup_id"), nullable=False, index=True)
    status: Mapped[RestoreStatus] = mapped_column(Enum(RestoreStatus), default=RestoreStatus.PENDING, nullable=False, index=True)
    
    # Target
    target_database: Mapped[str] = mapped_column(String(255), nullable=False)
    target_schema: Mapped[str] = mapped_column(String(100), default="public", nullable=False)
    tables_to_restore: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    point_in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Progress
    tables_restored: Mapped[int] = mapped_column(Integer, default=0)
    total_tables: Mapped[int] = mapped_column(Integer, default=0)
    rows_restored: Mapped[int] = mapped_column(Integer, default=0)
    
    # Validation
    validation_passed: Mapped[bool] = mapped_column(default=False)
    validation_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Error info
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    backup: Mapped["BackupRecord"] = relationship("BackupRecord")
    
    __table_args__ = (
        Index("ix_restore_records_backup_status", "backup_id", "status"),
    )
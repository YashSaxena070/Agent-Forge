"""
Disaster Recovery - Backup and Restore Procedures
"""
import asyncio
import gzip
import hashlib
import json
import os
import shutil
import tarfile
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional
from uuid import UUID, uuid4

import asyncpg
import boto3
from pydantic import BaseModel, Field

from apps.backend.src.core.config import settings
from apps.backend.src.core.database import db_manager
from apps.backend.src.core.audit import audit_log, AuditEventType, AuditSeverity
from apps.backend.src.core.tools import get_tool_executor


class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class BackupStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class RestoreStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATING = "validating"


class StorageBackend(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE_BLOB = "azure_blob"
    MINIO = "minio"


@dataclass
class BackupConfig:
    """Backup configuration."""
    name: str
    backup_type: BackupType
    schedule: str  # Cron expression
    retention_days: int
    storage_backend: StorageBackend
    storage_config: Dict[str, Any]
    include_tables: List[str] = field(default_factory=list)
    exclude_tables: List[str] = field(default_factory=list)
    compress: bool = True
    encrypt: bool = True
    max_parallel_jobs: int = 4
    timeout_hours: int = 24
    notification_emails: List[str] = field(default_factory=list)


@dataclass
class BackupRecord:
    """Backup execution record."""
    backup_id: UUID = field(default_factory=uuid4)
    config_name: str
    backup_type: BackupType
    status: BackupStatus
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    # Storage
    storage_backend: StorageBackend
    storage_path: str
    size_bytes: int = 0
    compressed_size_bytes: int = 0
    checksum: str = ""
    
    # Metadata
    tables_included: List[str] = field(default_factory=list)
    row_counts: Dict[str, int] = field(default_factory=dict)
    schema_version: str = ""
    
    # Error info
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    # Retention
    expires_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class RestoreRecord:
    """Restore execution record."""
    restore_id: UUID = field(default_factory=uuid4)
    backup_id: UUID
    status: RestoreStatus
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    # Target
    target_database: str
    target_schema: str = "public"
    tables_to_restore: List[str] = field(default_factory=list)
    point_in_time: Optional[datetime] = None
    
    # Progress
    tables_restored: int = 0
    total_tables: int = 0
    rows_restored: int = 0
    
    # Validation
    validation_passed: bool = False
    validation_details: Dict[str, Any] = field(default_factory=dict)
    
    # Error info
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)


class BackupManager:
    """Manages database backups and restores."""
    
    def __init__(self):
        self.configs: Dict[str, BackupConfig] = {}
        self.backup_records: Dict[UUID, BackupRecord] = {}
        self.restore_records: Dict[UUID, RestoreRecord] = {}
        self._running = False
        self._scheduler_task = None
    
    def register_config(self, config: BackupConfig):
        """Register a backup configuration."""
        self.configs[config.name] = config
    
    async def initialize(self):
        """Initialize backup manager."""
        # Load default configs from environment
        self._load_default_configs()
        
        # Start scheduler
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        
        # Load existing records
        await self._load_records()
    
    def _load_default_configs(self):
        """Load default backup configs from environment."""
        # Daily full backup
        self.register_config(BackupConfig(
            name="daily_full",
            backup_type=BackupType.FULL,
            schedule="0 2 * * *",  # 2 AM daily
            retention_days=30,
            storage_backend=StorageBackend.MINIO,
            storage_config={
                "endpoint": settings.MINIO_ENDPOINT,
                "access_key": settings.MINIO_ACCESS_KEY,
                "secret_key": settings.MINIO_SECRET_KEY,
                "bucket": "agentforge-backups",
                "prefix": "daily/",
            },
            compress=True,
            encrypt=True,
        ))
        
        # Hourly incremental
        self.register_config(BackupConfig(
            name="hourly_incremental",
            backup_type=BackupType.INCREMENTAL,
            schedule="0 * * * *",  # Every hour
            retention_days=7,
            storage_backend=StorageBackend.MINIO,
            storage_config={
                "endpoint": settings.MINIO_ENDPOINT,
                "access_key": settings.MINIO_ACCESS_KEY,
                "secret_key": settings.MINIO_SECRET_KEY,
                "bucket": "agentforge-backups",
                "prefix": "incremental/",
            },
            compress=True,
            encrypt=True,
        ))
        
        # Weekly snapshot
        self.register_config(BackupConfig(
            name="weekly_snapshot",
            backup_type=BackupType.SNAPSHOT,
            schedule="0 3 * * 0",  # 3 AM Sunday
            retention_days=90,
            storage_backend=StorageBackend.S3,
            storage_config={
                "bucket": settings.BACKUP_S3_BUCKET or "agentforge-snapshots",
                "prefix": "snapshots/",
                "region": "us-east-1",
            },
            compress=True,
            encrypt=True,
        ))
    
    async def _load_records(self):
        """Load backup/restore records from database."""
        async with db_manager.session() as session:
            from apps.backend.src.models.entities.disaster_recovery import BackupRecordModel, RestoreRecordModel
            
            # Load recent backups
            result = await session.execute(
                select(BackupRecordModel)
                .where(BackupRecordModel.started_at >= datetime.now(timezone.utc) - timedelta(days=30))
                .order_by(BackupRecordModel.started_at.desc())
            )
            for record in result.scalars().all():
                self.backup_records[record.backup_id] = self._model_to_record(record)
            
            # Load recent restores
            result = await session.execute(
                select(RestoreRecordModel)
                .where(RestoreRecordModel.started_at >= datetime.now(timezone.utc) - timedelta(days=30))
                .order_by(RestoreRecordModel.started_at.desc())
            )
            for record in result.scalars().all():
                self.restore_records[record.restore_id] = self._model_to_restore_record(record)
    
    def _model_to_record(self, model) -> BackupRecord:
        return BackupRecord(
            backup_id=model.backup_id,
            config_name=model.config_name,
            backup_type=model.backup_type,
            status=model.status,
            started_at=model.started_at,
            completed_at=model.completed_at,
            storage_backend=model.storage_backend,
            storage_path=model.storage_path,
            size_bytes=model.size_bytes,
            compressed_size_bytes=model.compressed_size_bytes,
            checksum=model.checksum,
            tables_included=model.tables_included,
            row_counts=model.row_counts,
            schema_version=model.schema_version,
            error_message=model.error_message,
            error_details=model.error_details,
            expires_at=model.expires_at,
            tags=model.tags,
        )
    
    def _model_to_restore_record(self, model) -> RestoreRecord:
        return RestoreRecord(
            restore_id=model.restore_id,
            backup_id=model.backup_id,
            status=model.status,
            started_at=model.started_at,
            completed_at=model.completed_at,
            target_database=model.target_database,
            target_schema=model.target_schema,
            tables_to_restore=model.tables_to_restore,
            point_in_time=model.point_in_time,
            tables_restored=model.tables_restored,
            total_tables=model.total_tables,
            rows_restored=model.rows_restored,
            validation_passed=model.validation_passed,
            validation_details=model.validation_details,
            error_message=model.error_message,
            error_details=model.error_details,
        )
    
    async def _save_record(self, record: BackupRecord):
        """Save backup record to database."""
        async with db_manager.session() as session:
            from apps.backend.src.models.entities.disaster_recovery import BackupRecordModel
            
            model = BackupRecordModel(
                backup_id=record.backup_id,
                config_name=record.config_name,
                backup_type=record.backup_type.value,
                status=record.status.value,
                started_at=record.started_at,
                completed_at=record.completed_at,
                storage_backend=record.storage_backend.value,
                storage_path=record.storage_path,
                size_bytes=record.size_bytes,
                compressed_size_bytes=record.compressed_size_bytes,
                checksum=record.checksum,
                tables_included=record.tables_included,
                row_counts=record.row_counts,
                schema_version=record.schema_version,
                error_message=record.error_message,
                error_details=record.error_details,
                expires_at=record.expires_at,
                tags=record.tags,
            )
            session.add(model)
            await session.commit()
        
        self.backup_records[record.backup_id] = record
    
    async def _save_restore_record(self, record: RestoreRecord):
        """Save restore record to database."""
        async with db_manager.session() as session:
            from apps.backend.src.models.entities.disaster_recovery import RestoreRecordModel
            
            model = RestoreRecordModel(
                restore_id=record.restore_id,
                backup_id=record.backup_id,
                status=record.status.value,
                started_at=record.started_at,
                completed_at=record.completed_at,
                target_database=record.target_database,
                target_schema=record.target_schema,
                tables_to_restore=record.tables_to_restore,
                point_in_time=record.point_in_time,
                tables_restored=record.tables_restored,
                total_tables=record.total_tables,
                rows_restored=record.rows_restored,
                validation_passed=record.validation_passed,
                validation_details=record.validation_details,
                error_message=record.error_message,
                error_details=record.error_details,
            )
            session.add(model)
            await session.commit()
        
        self.restore_records[record.restore_id] = record
    
    async def _run_scheduler(self):
        """Run backup scheduler."""
        self._running = True
        while self._running:
            try:
                await self._check_schedules()
            except Exception as e:
                print(f"Scheduler error: {e}")
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_schedules(self):
        """Check if any backup configs are due to run."""
        from croniter import croniter
        
        now = datetime.now(timezone.utc)
        
        for config in self.configs.values():
            try:
                cron = croniter(config.schedule, now - timedelta(minutes=1))
                next_run = cron.get_next(datetime)
                
                # Check if it's time to run (within 1 minute)
                if abs((next_run - now).total_seconds()) < 60:
                    # Check if already running
                    running = any(
                        r.status == BackupStatus.RUNNING and r.config_name == config.name
                        for r in self.backup_records.values()
                    )
                    
                    if not running:
                        asyncio.create_task(self.run_backup(config.name))
            except Exception as e:
                print(f"Schedule check error for {config.name}: {e}")
    
    async def run_backup(self, config_name: str) -> BackupRecord:
        """Execute a backup."""
        config = self.configs.get(config_name)
        if not config:
            raise ValueError(f"Backup config not found: {config_name}")
        
        record = BackupRecord(
            config_name=config.name,
            backup_type=config.backup_type,
            status=BackupStatus.RUNNING,
            storage_backend=config.storage_backend,
            expires_at=datetime.now(timezone.utc) + timedelta(days=config.retention_days),
        )
        
        await self._save_record(record)
        
        # Audit log
        await audit_log(
            event_type=AuditEventType.BACKUP_CREATED,
            action="backup.started",
            resource_type="backup",
            resource_id=record.backup_id,
            details={"config": config.name, "type": config.backup_type.value},
            severity=AuditSeverity.MEDIUM,
            compliance_tags=["disaster_recovery", "backup"],
        )
        
        try:
            # Execute backup based on type
            if config.backup_type == BackupType.FULL:
                await self._run_full_backup(record, config)
            elif config.backup_type == BackupType.INCREMENTAL:
                await self._run_incremental_backup(record, config)
            elif config.backup_type == BackupType.SNAPSHOT:
                await self._run_snapshot_backup(record, config)
            elif config.backup_type == BackupType.DIFFERENTIAL:
                await self._run_differential_backup(record, config)
            
            record.status = BackupStatus.COMPLETED
            record.completed_at = datetime.now(timezone.utc)
            
        except Exception as e:
            record.status = BackupStatus.FAILED
            record.completed_at = datetime.now(timezone.utc)
            record.error_message = str(e)
            record.error_details = {"exception": type(e).__name__}
            
            # Audit log
            await audit_log(
                event_type=AuditEventType.BACKUP_CREATED,
                action="backup.failed",
                resource_type="backup",
                resource_id=record.backup_id,
                outcome="failure",
                details={"error": str(e)},
                severity=AuditSeverity.CRITICAL,
                compliance_tags=["disaster_recovery", "backup"],
            )
            
            raise
        
        finally:
            await self._save_record(record)
        
        return record
    
    async def _run_full_backup(self, record: BackupRecord, config: BackupConfig):
        """Run full database backup using pg_dump."""
        # Get database connection info
        db_url = settings.DATABASE_URL
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            dump_file = Path(tmpdir) / f"full_backup_{record.backup_id}.sql"
            
            # Run pg_dump
            cmd = [
                "pg_dump",
                "--no-owner",
                "--no-privileges",
                "--format=custom",
                "--compress=9",
                f"--file={dump_file}",
                db_url,
            ]
            
            if config.exclude_tables:
                for table in config.exclude_tables:
                    cmd.extend(["--exclude-table", table])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {stderr.decode()}")
            
            # Get file size and checksum
            size = dump_file.stat().st_size
            checksum = await self._compute_checksum(dump_file)
            
            # Compress if needed
            if config.compress:
                compressed_file = dump_file.with_suffix(".sql.gz")
                with open(dump_file, "rb") as f_in:
                    with gzip.open(compressed_file, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                dump_file = compressed_file
                compressed_size = dump_file.stat().st_size
            else:
                compressed_size = size
            
            # Encrypt if needed
            if config.encrypt:
                encrypted_file = await self._encrypt_file(dump_file)
                dump_file = encrypted_file
            
            # Upload to storage
            storage_path = await self._upload_to_storage(
                dump_file,
                config.storage_backend,
                config.storage_config,
                f"{config.storage_config.get('prefix', '')}{record.backup_id}.sql{'gz' if config.compress else ''}",
            )
            
            # Update record
            record.storage_path = storage_path
            record.size_bytes = size
            record.compressed_size_bytes = compressed_size
            record.checksum = checksum
            record.tables_included = await self._get_table_list()
            record.row_counts = await self._get_row_counts()
            record.schema_version = await self._get_schema_version()
    
    async def _run_incremental_backup(self, record: BackupRecord, config: BackupConfig):
        """Run incremental backup using WAL archiving."""
        # This would use pg_basebackup or WAL-G for incremental backups
        # Simplified implementation
        pass
    
    async def _run_snapshot_backup(self, record: BackupRecord, config: BackupConfig):
        """Run snapshot backup (e.g., EBS snapshot, Cloud SQL export)."""
        pass
    
    async def _run_differential_backup(self, record: BackupRecord, config: BackupConfig):
        """Run differential backup."""
        pass
    
    async def restore_backup(
        self,
        backup_id: UUID,
        target_database: str,
        target_schema: str = "public",
        tables: List[str] = None,
        point_in_time: datetime = None,
    ) -> RestoreRecord:
        """Restore from a backup."""
        record = self.backup_records.get(backup_id)
        if not record:
            raise ValueError(f"Backup not found: {backup_id}")
        
        if record.status != BackupStatus.COMPLETED:
            raise ValueError(f"Backup not completed: {backup_id}")
        
        restore_record = RestoreRecord(
            backup_id=backup_id,
            status=RestoreStatus.RUNNING,
            target_database=target_database,
            target_schema=target_schema,
            tables_to_restore=tables or [],
        )
        
        await self._save_restore_record(restore_record)
        
        # Audit log
        await audit_log(
            event_type=AuditEventType.RESTORE_INITIATED,
            action="restore.started",
            resource_type="restore",
            resource_id=restore_record.restore_id,
            details={"backup_id": str(backup_id), "target": target_database},
            severity=AuditSeverity.HIGH,
            compliance_tags=["disaster_recovery", "restore"],
        )
        
        try:
            # Download backup from storage
            backup_file = await self._download_from_storage(
                record.storage_path,
                record.storage_backend,
                record.storage_config,
            )
            
            # Decrypt if needed
            if record.checksum:  # Assume encrypted if checksum exists
                backup_file = await self._decrypt_file(backup_file)
            
            # Decompress if needed
            if backup_file.suffix == ".gz":
                backup_file = await self._decompress_file(backup_file)
            
            # Verify checksum
            if not await self._verify_checksum(backup_file, record.checksum):
                raise ValueError("Checksum verification failed")
            
            # Restore using pg_restore
            await self._run_restore(backup_file, target_database, target_schema, tables)
            
            # Validate restore
            await self._validate_restore(target_database, tables)
            
            restore_record.status = RestoreStatus.COMPLETED
            restore_record.completed_at = datetime.now(timezone.utc)
            restore_record.validation_passed = True
            
        except Exception as e:
            restore_record.status = RestoreStatus.FAILED
            restore_record.completed_at = datetime.now(timezone.utc)
            restore_record.error_message = str(e)
            raise
        
        finally:
            await self._save_restore_record(restore_record)
        
        return restore_record
    
    async def _run_restore(
        self,
        backup_file: Path,
        target_database: str,
        target_schema: str,
        tables: List[str] = None,
    ):
        """Run pg_restore."""
        cmd = [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            f"--dbname={target_database}",
            f"--schema={target_schema}",
        ]
        
        if tables:
            for table in tables:
                cmd.extend(["--table", table])
        
        cmd.append(str(backup_file))
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"pg_restore failed: {stderr.decode()}")
    
    async def _validate_restore(self, target_database: str, tables: List[str] = None):
        """Validate restored database."""
        conn = await asyncpg.connect(target_database)
        try:
            if tables:
                for table in tables:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    print(f"Table {table}: {count} rows")
            else:
                # Check all tables
                tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                for table in tables:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['tablename']}")
                    print(f"Table {table['tablename']}: {count} rows")
        finally:
            await conn.close()
    
    async def _compute_checksum(self, file_path: Path) -> str:
        """Compute SHA256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def _verify_checksum(self, file_path: Path, expected: str) -> bool:
        """Verify file checksum."""
        computed = await self._compute_checksum(file_path)
        return hmac.compare_digest(computed, expected)
    
    async def _encrypt_file(self, file_path: Path) -> Path:
        """Encrypt file using AES-256-GCM."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        key = settings.ENCRYPTION_KEY.encode()[:32]
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)
        
        with open(file_path, "rb") as f:
            plaintext = f.read()
        
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        encrypted_path = file_path.with_suffix(file_path.suffix + ".enc")
        with open(encrypted_path, "wb") as f:
            f.write(nonce + ciphertext)
        
        return encrypted_path
    
    async def _decrypt_file(self, file_path: Path) -> Path:
        """Decrypt file."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        key = settings.ENCRYPTION_KEY.encode()[:32]
        aesgcm = AESGCM(key)
        
        with open(file_path, "rb") as f:
            data = f.read()
        
        nonce = data[:12]
        ciphertext = data[12:]
        
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        decrypted_path = file_path.with_suffix("")
        with open(decrypted_path, "wb") as f:
            f.write(plaintext)
        
        return decrypted_path
    
    async def _compress_file(self, file_path: Path) -> Path:
        """Compress file with gzip."""
        compressed_path = file_path.with_suffix(file_path.suffix + ".gz")
        with open(file_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return compressed_path
    
    async def _decompress_file(self, file_path: Path) -> Path:
        """Decompress gzip file."""
        decompressed_path = file_path.with_suffix("")
        with gzip.open(file_path, "rb") as f_in:
            with open(decompressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return decompressed_path
    
    async def _upload_to_storage(
        self,
        file_path: Path,
        backend: StorageBackend,
        config: Dict[str, Any],
        object_name: str,
    ) -> str:
        """Upload file to storage backend."""
        if backend == StorageBackend.MINIO or backend == StorageBackend.S3:
            return await self._upload_to_s3(file_path, config, object_name)
        elif backend == StorageBackend.LOCAL:
            return await self._upload_to_local(file_path, config, object_name)
        else:
            raise ValueError(f"Unsupported storage backend: {backend}")
    
    async def _upload_to_s3(self, file_path: Path, config: Dict, object_name: str) -> str:
        """Upload to S3-compatible storage."""
        s3_client = boto3.client(
            "s3",
            endpoint_url=config.get("endpoint"),
            aws_access_key_id=config.get("access_key"),
            aws_secret_access_key=config.get("secret_key"),
            region_name=config.get("region", "us-east-1"),
        )
        
        bucket = config["bucket"]
        key = f"{config.get('prefix', '')}{object_name}"
        
        s3_client.upload_file(str(file_path), bucket, key)
        
        return f"s3://{bucket}/{key}"
    
    async def _upload_to_local(self, file_path: Path, config: Dict, object_name: str) -> str:
        """Copy to local storage."""
        dest_dir = Path(config.get("path", "/backups"))
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / object_name
        shutil.copy2(file_path, dest_path)
        return f"file://{dest_path}"
    
    async def _download_from_storage(
        self,
        storage_path: str,
        backend: StorageBackend,
        config: Dict,
    ) -> Path:
        """Download file from storage."""
        if backend == StorageBackend.MINIO or backend == StorageBackend.S3:
            return await self._download_from_s3(storage_path, config)
        elif backend == StorageBackend.LOCAL:
            return await self._download_from_local(storage_path)
        else:
            raise ValueError(f"Unsupported storage backend: {backend}")
    
    async def _download_from_s3(self, storage_path: str, config: Dict) -> Path:
        """Download from S3."""
        # Parse s3://bucket/key
        path = storage_path.replace("s3://", "")
        bucket, key = path.split("/", 1)
        
        s3_client = boto3.client(
            "s3",
            endpoint_url=config.get("endpoint"),
            aws_access_key_id=config.get("access_key"),
            aws_secret_access_key=config.get("secret_key"),
            region_name=config.get("region", "us-east-1"),
        )
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            s3_client.download_file(bucket, key, tmp.name)
            return Path(tmp.name)
    
    async def _download_from_local(self, storage_path: str) -> Path:
        """Copy from local storage."""
        src = Path(storage_path.replace("file://", ""))
        dst = Path(tempfile.mktemp())
        shutil.copy2(src, dst)
        return dst
    
    async def _get_table_list(self) -> List[str]:
        """Get list of tables in database."""
        async with db_manager.session() as session:
            result = await session.execute(text("""
                SELECT tablename FROM pg_tables WHERE schemaname = 'public'
            """))
            return [row[0] for row in result.fetchall()]
    
    async def _get_row_counts(self) -> Dict[str, int]:
        """Get row counts for all tables."""
        counts = {}
        async with db_manager.session() as session:
            tables = await self._get_table_list()
            for table in tables:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar()
        return counts
    
    async def _get_schema_version(self) -> str:
        """Get current schema version from alembic."""
        async with db_manager.session() as session:
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            return result.scalar() or "unknown"
    
    def get_backup_status(self, backup_id: UUID) -> Optional[BackupRecord]:
        """Get backup record by ID."""
        return self.backup_records.get(backup_id)
    
    def get_restore_status(self, restore_id: UUID) -> Optional[RestoreRecord]:
        """Get restore record by ID."""
        return self.restore_records.get(restore_id)
    
    def list_backups(self, config_name: str = None) -> List[BackupRecord]:
        """List backup records."""
        records = list(self.backup_records.values())
        if config_name:
            records = [r for r in records if r.config_name == config_name]
        return sorted(records, key=lambda r: r.started_at, reverse=True)
    
    def list_restores(self) -> List[RestoreRecord]:
        """List restore records."""
        return sorted(self.restore_records.values(), key=lambda r: r.started_at, reverse=True)
    
    async def cleanup_expired_backups(self):
        """Delete expired backups."""
        now = datetime.now(timezone.utc)
        
        for record in list(self.backup_records.values()):
            if record.expires_at and record.expires_at <= now:
                # Delete from storage
                await self._delete_from_storage(record.storage_path, record.storage_backend)
                
                # Delete record
                del self.backup_records[record.backup_id]
                
                # Audit log
                await audit_log(
                    event_type=AuditEventType.BACKUP_CREATED,
                    action="backup.expired_deleted",
                    resource_type="backup",
                    resource_id=record.backup_id,
                    severity=AuditSeverity.LOW,
                    compliance_tags=["disaster_recovery", "backup"],
                )
    
    async def shutdown(self):
        """Shutdown backup manager."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass


# Disaster Recovery Plan Document
class DRPlan(BaseModel):
    """Disaster Recovery Plan document."""
    plan_id: UUID = Field(default_factory=uuid4)
    name: str
    version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # RTO/RPO
    rto_hours: int = 4  # Recovery Time Objective
    rpo_hours: int = 1  # Recovery Point Objective
    
    # Contacts
    primary_contact: Dict[str, str]
    secondary_contact: Dict[str, str]
    escalation_contacts: List[Dict[str, str]] = Field(default_factory=list)
    
    # Infrastructure
    primary_region: str
    dr_region: str
    failover_dns: str
    
    # Procedures
    failover_steps: List[str]
    failback_steps: List[str]
    validation_steps: List[str]
    
    # Dependencies
    critical_services: List[str]
    external_dependencies: List[str]
    
    # Testing
    last_test_date: Optional[datetime] = None
    next_test_date: Optional[datetime] = None
    test_results: List[Dict[str, Any]] = Field(default_factory=list)


# Global instances
backup_manager = BackupManager()


async def initialize_disaster_recovery():
    """Initialize disaster recovery system."""
    await backup_manager.initialize()
    
    # Schedule cleanup task
    asyncio.create_task(_periodic_cleanup())
    
    return backup_manager


async def _periodic_cleanup():
    """Periodic cleanup of expired backups."""
    while True:
        await asyncio.sleep(3600)  # Every hour
        try:
            await backup_manager.cleanup_expired_backups()
        except Exception as e:
            print(f"Cleanup error: {e}")


async def create_backup(config_name: str = "daily_full") -> BackupRecord:
    """Create a backup."""
    return await backup_manager.run_backup(config_name)


async def restore_from_backup(
    backup_id: UUID,
    target_database: str,
    **kwargs,
) -> RestoreRecord:
    """Restore from backup."""
    return await backup_manager.restore_backup(backup_id, target_database, **kwargs)


async def get_backup_status(backup_id: UUID) -> Optional[BackupRecord]:
    return backup_manager.get_backup_status(backup_id)


async def list_backups(config_name: str = None) -> List[BackupRecord]:
    return backup_manager.list_backups(config_name)


import tempfile
from pathlib import Path
import hmac
import secrets
from sqlalchemy import text, select
from apps.backend.src.models.entities.disaster_recovery import BackupRecordModel, RestoreRecordModel
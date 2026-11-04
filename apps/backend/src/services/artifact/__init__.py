"""
Artifact service for managing artifacts.
"""
import os
import aiofiles
from typing import Optional, BinaryIO
from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.core.config import settings
from apps.backend.src.models.entities import Artifact, ArtifactType
from apps.backend.src.core.exceptions import NotFoundError


class ArtifactService:
    """Service for artifact operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage_path = Path(settings.ARTIFACT_STORAGE_PATH) if hasattr(settings, 'ARTIFACT_STORAGE_PATH') else Path("/tmp/agentforge/artifacts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def create_artifact(
        self,
        task_id: UUID,
        project_id: UUID,
        created_by: UUID,
        name: str,
        type: ArtifactType,
        content: str,
        metadata: dict = None,
        file_path: str = None,
        mime_type: str = None,
    ) -> Artifact:
        """Create a new artifact."""
        artifact = Artifact(
            task_id=task_id,
            project_id=project_id,
            created_by=created_by,
            name=name,
            type=type,
            content=content,
            metadata=metadata or {},
            file_path=file_path,
            mime_type=mime_type,
            size_bytes=len(content.encode('utf-8')) if content else 0,
        )
        
        self.db.add(artifact)
        await self.db.commit()
        await self.db.refresh(artifact)
        
        return artifact
    
    async def store_artifact_file(self, artifact_id: UUID, content: bytes) -> str:
        """Store artifact file content."""
        artifact = await self.get_artifact(artifact_id)
        if not artifact:
            raise NotFoundError("Artifact", artifact_id)
        
        file_path = self.storage_path / str(artifact.project_id) / str(artifact_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        artifact.file_path = str(file_path)
        artifact.size_bytes = len(content)
        artifact.mime_type = artifact.mime_type or "application/octet-stream"
        
        await self.db.commit()
        await self.db.refresh(artifact)
        
        return str(file_path)
    
    async def get_artifact_file(self, artifact_id: UUID) -> Optional[bytes]:
        """Get artifact file content."""
        artifact = await self.get_artifact(artifact_id)
        if not artifact or not artifact.file_path:
            return None
        
        file_path = Path(artifact.file_path)
        if not file_path.exists():
            return None
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def get_artifact(self, artifact_id: UUID) -> Optional[Artifact]:
        """Get artifact by ID."""
        result = await self.db.execute(
            select(Artifact).where(Artifact.id == artifact_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_artifact(self, artifact_id: UUID) -> bool:
        """Delete artifact and its file."""
        artifact = await self.get_artifact(artifact_id)
        if not artifact:
            return False
        
        # Delete file if exists
        if artifact.file_path:
            file_path = Path(artifact.file_path)
            if file_path.exists():
                file_path.unlink()
        
        await self.db.delete(artifact)
        await self.db.commit()
        
        return True
    
    async def create_artifact_version(
        self,
        artifact_id: UUID,
        content: str,
        metadata: dict = None,
    ) -> Artifact:
        """Create a new version of an artifact."""
        artifact = await self.get_artifact(artifact_id)
        if not artifact:
            raise NotFoundError("Artifact", artifact_id)
        
        new_artifact = Artifact(
            task_id=artifact.task_id,
            project_id=artifact.project_id,
            created_by=artifact.created_by,
            name=artifact.name,
            type=artifact.type,
            content=content,
            metadata=metadata or artifact.metadata,
            file_path=artifact.file_path,
            mime_type=artifact.mime_type,
            size_bytes=len(content.encode('utf-8')) if content else 0,
            version=artifact.version + 1,
            parent_id=artifact.id,
        )
        
        self.db.add(new_artifact)
        await self.db.commit()
        await self.db.refresh(new_artifact)
        
        return new_artifact


from pathlib import Path
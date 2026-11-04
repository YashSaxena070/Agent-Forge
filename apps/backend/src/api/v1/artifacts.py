"""
Artifact management endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.core.database import get_db_session
from apps.backend.src.core.security import (
    Permission,
    require_permission,
    verify_token,
)
from apps.backend.src.core.exceptions import NotFoundError
from apps.backend.src.models.entities import Artifact, Task, Project, User
from apps.backend.src.services.artifact import ArtifactService
from apps.backend.src.models.schemas import ArtifactCreate, Artifact as ArtifactSchema

router = APIRouter()


async def get_current_user(
    token: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Get current user from token."""
    from apps.backend.src.models.entities import User
    result = await db.execute(select(User).where(User.id == UUID(token.sub)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=ArtifactSchema, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    artifact_data: ArtifactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new artifact."""
    require_permission(current_user.token_data, Permission.WORKFLOW_CREATE)
    
    # Verify task exists and user has access
    result = await db.execute(
        select(Task)
        .join(Project)
        .where(Task.id == artifact_data.task_id, Project.owner_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", artifact_data.task_id)
    
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.create_artifact(
        task_id=artifact_data.task_id,
        project_id=artifact_data.project_id,
        created_by=current_user.id,
        name=artifact_data.name,
        type=artifact_data.type,
        content=artifact_data.content,
        metadata=artifact_data.metadata,
        file_path=artifact_data.file_path,
        mime_type=artifact_data.mime_type,
    )
    
    return artifact


@router.post("/upload", response_model=ArtifactSchema, status_code=status.HTTP_201_CREATED)
async def upload_artifact(
    task_id: UUID,
    project_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Upload an artifact file."""
    require_permission(current_user.token_data, Permission.WORKFLOW_CREATE)
    
    # Verify task exists and user has access
    result = await db.execute(
        select(Task)
        .join(Project)
        .where(Task.id == task_id, Project.owner_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_id)
    
    content = await file.read()
    
    artifact_service = ArtifactService(db)
    artifact = await artifact_service.create_artifact(
        task_id=task_id,
        project_id=project_id,
        created_by=current_user.id,
        name=file.filename or "uploaded_file",
        type="code",  # Default type
        content=content.decode("utf-8", errors="ignore"),
        file_path=None,  # Will be set by service
        mime_type=file.content_type,
    )
    
    # Store file content
    await artifact_service.store_artifact_file(artifact.id, content)
    
    return artifact


@router.get("", response_model=List[ArtifactSchema])
async def list_artifacts(
    project_id: Optional[UUID] = None,
    task_id: Optional[UUID] = None,
    type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List artifacts with filtering."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    query = select(Artifact).join(Project).where(Project.owner_id == current_user.id)
    
    if project_id:
        query = query.where(Artifact.project_id == project_id)
    
    if task_id:
        query = query.where(Artifact.task_id == task_id)
    
    if type:
        query = query.where(Artifact.type == type)
    
    query = query.offset(skip).limit(limit).order_by(Artifact.created_at.desc())
    
    result = await db.execute(query)
    artifacts = result.scalars().all()
    
    return artifacts


@router.get("/{artifact_id}", response_model=ArtifactSchema)
async def get_artifact(
    artifact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get an artifact by ID."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    result = await db.execute(
        select(Artifact)
        .join(Project)
        .where(Artifact.id == artifact_id, Project.owner_id == current_user.id)
    )
    artifact = result.scalar_one_or_none()
    
    if not artifact:
        raise NotFoundError("Artifact", artifact_id)
    
    return artifact


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Download an artifact file."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    result = await db.execute(
        select(Artifact)
        .join(Project)
        .where(Artifact.id == artifact_id, Project.owner_id == current_user.id)
    )
    artifact = result.scalar_one_or_none()
    
    if not artifact:
        raise NotFoundError("Artifact", artifact_id)
    
    artifact_service = ArtifactService(db)
    content = await artifact_service.get_artifact_file(artifact_id)
    
    if content is None:
        raise NotFoundError("Artifact file", artifact_id)
    
    return StreamingResponse(
        iter([content]),
        media_type=artifact.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={artifact.name}"},
    )


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artifact(
    artifact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete an artifact."""
    require_permission(current_user.token_data, Permission.WORKFLOW_UPDATE)
    
    result = await db.execute(
        select(Artifact)
        .join(Project)
        .where(Artifact.id == artifact_id, Project.owner_id == current_user.id)
    )
    artifact = result.scalar_one_or_none()
    
    if not artifact:
        raise NotFoundError("Artifact", artifact_id)
    
    artifact_service = ArtifactService(db)
    await artifact_service.delete_artifact(artifact_id)
    
    await db.delete(artifact)
    await db.commit()
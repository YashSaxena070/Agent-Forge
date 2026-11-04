"""
Task management endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.backend.src.core.database import get_db_session
from apps.backend.src.core.security import (
    Permission,
    require_permission,
    verify_token,
)
from apps.backend.src.core.exceptions import NotFoundError
from apps.backend.src.models.entities import Task, Project, User, Workflow, Artifact
from apps.backend.src.models.schemas import TaskCreate, TaskUpdate, Task as TaskSchema
from services.shared.schemas import TaskStatus, AgentRole

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


@router.post("", response_model=TaskSchema, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new task."""
    require_permission(current_user.token_data, Permission.WORKFLOW_CREATE)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == task_data.project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", task_data.project_id)
    
    # Verify workflow if provided
    if task_data.workflow_id:
        result = await db.execute(
            select(Workflow).where(Workflow.id == task_data.workflow_id, Workflow.project_id == task_data.project_id)
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            raise NotFoundError("Workflow", task_data.workflow_id)
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        role=task_data.role,
        priority=task_data.priority,
        dependencies=task_data.dependencies,
        estimated_effort=task_data.estimated_effort,
        tags=task_data.tags,
        project_id=task_data.project_id,
        workflow_id=task_data.workflow_id,
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return task


@router.get("", response_model=List[TaskSchema])
async def list_tasks(
    project_id: Optional[UUID] = None,
    workflow_id: Optional[UUID] = None,
    status: Optional[TaskStatus] = None,
    role: Optional[AgentRole] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List tasks with filtering and pagination."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    query = select(Task).join(Project).where(Project.owner_id == current_user.id)
    
    if project_id:
        query = query.where(Task.project_id == project_id)
    
    if workflow_id:
        query = query.where(Task.workflow_id == workflow_id)
    
    if status:
        query = query.where(Task.status == status)
    
    if role:
        query = query.where(Task.role == role)
    
    query = query.offset(skip).limit(limit).order_by(Task.created_at.desc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return tasks


@router.get("/{task_id}", response_model=TaskSchema)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a task by ID."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.artifacts))
        .join(Project)
        .where(Task.id == task_id, Project.owner_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_id)
    
    return task


@router.patch("/{task_id}", response_model=TaskSchema)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a task."""
    require_permission(current_user.token_data, Permission.WORKFLOW_UPDATE)
    
    result = await db.execute(
        select(Task)
        .join(Project)
        .where(Task.id == task_id, Project.owner_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_id)
    
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a task."""
    require_permission(current_user.token_data, Permission.WORKFLOW_UPDATE)
    
    result = await db.execute(
        select(Task)
        .join(Project)
        .where(Task.id == task_id, Project.owner_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_id)
    
    await db.delete(task)
    await db.commit()


@router.get("/{task_id}/artifacts", response_model=List[dict])
async def get_task_artifacts(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get artifacts for a task."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    result = await db.execute(
        select(Task)
        .join(Project)
        .where(Task.id == task_id, Project.owner_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_id)
    
    artifacts_result = await db.execute(
        select(Artifact).where(Artifact.task_id == task_id)
    )
    artifacts = artifacts_result.scalars().all()
    
    return [
        {
            "id": str(artifact.id),
            "name": artifact.name,
            "type": artifact.type,
            "file_path": artifact.file_path,
            "mime_type": artifact.mime_type,
            "size_bytes": artifact.size_bytes,
            "created_at": artifact.created_at.isoformat(),
        }
        for artifact in artifacts
    ]


@router.post("/{task_id}/retry", status_code=status.HTTP_200_OK)
async def retry_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Retry a failed task."""
    require_permission(current_user.token_data, Permission.WORKFLOW_EXECUTE)
    
    result = await db.execute(
        select(Task)
        .join(Project)
        .where(Task.id == task_id, Project.owner_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_id)
    
    if task.status != TaskStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only failed tasks can be retried")
    
    task.status = TaskStatus.PENDING
    task.error = None
    task.progress = 0
    task.started_at = None
    task.completed_at = None
    
    await db.commit()
    await db.refresh(task)
    
    return {"message": "Task queued for retry", "task_id": str(task_id)}
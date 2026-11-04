"""
Workflow management endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.backend.src.core.database import get_db_session
from apps.backend.src.core.security import (
    TokenData,
    Permission,
    require_permission,
    verify_token,
)
from apps.backend.src.core.exceptions import NotFoundError, ConflictError, WorkflowError
from apps.backend.src.models.entities import Workflow, Project, User, Task
from apps.backend.src.models.schemas import WorkflowCreate, WorkflowUpdate, Workflow as WorkflowSchema
from apps.backend.src.services.workflow import WorkflowService
from apps.backend.src.orchestration.langgraph.executor import WorkflowExecutor

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


@router.post("", response_model=WorkflowSchema, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new workflow."""
    require_permission(current_user.token_data, Permission.WORKFLOW_CREATE)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == workflow_data.project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", workflow_data.project_id)
    
    workflow_service = WorkflowService(db)
    workflow = await workflow_service.create_workflow(
        project_id=workflow_data.project_id,
        name=workflow_data.name,
        description=workflow_data.description,
        initial_state=workflow_data.initial_state,
    )
    
    return workflow


@router.get("", response_model=List[WorkflowSchema])
async def list_workflows(
    project_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List workflows with pagination."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    query = select(Workflow).join(Project).where(Project.owner_id == current_user.id)
    
    if project_id:
        query = query.where(Workflow.project_id == project_id)
    
    if status:
        query = query.where(Workflow.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Workflow.created_at.desc())
    
    result = await db.execute(query)
    workflows = result.scalars().all()
    
    return workflows


@router.get("/{workflow_id}", response_model=WorkflowSchema)
async def get_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a workflow by ID."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    result = await db.execute(
        select(Workflow)
        .options(selectinload(Workflow.tasks), selectinload(Workflow.project))
        .join(Project)
        .where(Workflow.id == workflow_id, Project.owner_id == current_user.id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise NotFoundError("Workflow", workflow_id)
    
    return workflow


@router.patch("/{workflow_id}", response_model=WorkflowSchema)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a workflow."""
    require_permission(current_user.token_data, Permission.WORKFLOW_UPDATE)
    
    result = await db.execute(
        select(Workflow)
        .join(Project)
        .where(Workflow.id == workflow_id, Project.owner_id == current_user.id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise NotFoundError("Workflow", workflow_id)
    
    update_data = workflow_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    await db.commit()
    await db.refresh(workflow)
    
    return workflow


@router.post("/{workflow_id}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Execute a workflow."""
    require_permission(current_user.token_data, Permission.WORKFLOW_EXECUTE)
    
    result = await db.execute(
        select(Workflow)
        .join(Project)
        .where(Workflow.id == workflow_id, Project.owner_id == current_user.id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise NotFoundError("Workflow", workflow_id)
    
    if workflow.status == "running":
        raise ConflictError("Workflow is already running")
    
    # Execute workflow asynchronously
    executor = WorkflowExecutor(db)
    await executor.execute_workflow(workflow_id, current_user.id)
    
    return {"message": "Workflow execution started", "workflow_id": str(workflow_id)}


@router.post("/{workflow_id}/pause", status_code=status.HTTP_200_OK)
async def pause_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Pause a running workflow."""
    require_permission(current_user.token_data, Permission.WORKFLOW_UPDATE)
    
    workflow_service = WorkflowService(db)
    await workflow_service.pause_workflow(workflow_id)
    
    return {"message": "Workflow paused", "workflow_id": str(workflow_id)}


@router.post("/{workflow_id}/resume", status_code=status.HTTP_200_OK)
async def resume_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Resume a paused workflow."""
    require_permission(current_user.token_data, Permission.WORKFLOW_EXECUTE)
    
    workflow_service = WorkflowService(db)
    await workflow_service.resume_workflow(workflow_id)
    
    return {"message": "Workflow resumed", "workflow_id": str(workflow_id)}


@router.post("/{workflow_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Cancel a workflow."""
    require_permission(current_user.token_data, Permission.WORKFLOW_UPDATE)
    
    workflow_service = WorkflowService(db)
    await workflow_service.cancel_workflow(workflow_id)
    
    return {"message": "Workflow cancelled", "workflow_id": str(workflow_id)}


@router.get("/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get workflow execution status."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    result = await db.execute(
        select(Workflow)
        .join(Project)
        .where(Workflow.id == workflow_id, Project.owner_id == current_user.id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise NotFoundError("Workflow", workflow_id)
    
    # Get task statuses
    tasks_result = await db.execute(
        select(Task).where(Task.workflow_id == workflow_id)
    )
    tasks = tasks_result.scalars().all()
    
    return {
        "workflow_id": str(workflow_id),
        "status": workflow.status,
        "phase": workflow.current_phase,
        "progress": workflow.progress,
        "tasks": [
            {
                "id": str(task.id),
                "title": task.title,
                "status": task.status,
                "progress": task.progress,
                "agent_role": task.role,
            }
            for task in tasks
        ],
    }


@router.get("/{workflow_id}/logs")
async def get_workflow_logs(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get workflow execution logs."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    result = await db.execute(
        select(Workflow)
        .join(Project)
        .where(Workflow.id == workflow_id, Project.owner_id == current_user.id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise NotFoundError("Workflow", workflow_id)
    
    # In a real implementation, logs would be stored separately
    return {
        "workflow_id": str(workflow_id),
        "logs": workflow.state.get("logs", []),
    }
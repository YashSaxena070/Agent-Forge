"""
Project management endpoints.
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
from apps.backend.src.core.exceptions import NotFoundError, ConflictError
from apps.backend.src.models.entities import Project, User
from apps.backend.src.models.schemas import ProjectCreate, ProjectUpdate, Project as ProjectSchema
from apps.backend.src.services.workflow import WorkflowService
from services.shared.schemas import Project as SharedProject

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


@router.post("", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new project."""
    require_permission(current_user.token_data, Permission.PROJECT_CREATE)
    
    project = Project(
        name=project_data.name,
        description=project_data.description,
        repository_url=project_data.repository_url,
        technology_stack=project_data.technology_stack,
        requirements=project_data.requirements,
        owner_id=current_user.id,
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project


@router.get("", response_model=List[ProjectSchema])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List projects with pagination."""
    require_permission(current_user.token_data, Permission.PROJECT_LIST)
    
    query = select(Project).where(Project.owner_id == current_user.id)
    
    if status:
        query = query.where(Project.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return projects


@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a project by ID."""
    require_permission(current_user.token_data, Permission.PROJECT_READ)
    
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.workflows))
        .where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    return project


@router.patch("/{project_id}", response_model=ProjectSchema)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update a project."""
    require_permission(current_user.token_data, Permission.PROJECT_UPDATE)
    
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a project."""
    require_permission(current_user.token_data, Permission.PROJECT_DELETE)
    
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/workflows", status_code=status.HTTP_201_CREATED)
async def create_workflow_for_project(
    project_id: UUID,
    workflow_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a workflow for a project."""
    require_permission(current_user.token_data, Permission.WORKFLOW_CREATE)
    
    # Verify project exists
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    workflow_service = WorkflowService(db)
    workflow = await workflow_service.create_workflow(
        project_id=project_id,
        name=workflow_data.get("name"),
        description=workflow_data.get("description"),
        initial_state=workflow_data.get("initial_state", {}),
    )
    
    return workflow
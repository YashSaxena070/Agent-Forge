"""
Deployment management endpoints.
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
from apps.backend.src.core.exceptions import NotFoundError, DeploymentError
from apps.backend.src.models.entities import Deployment, Project, User, Workflow
from apps.backend.src.models.schemas import DeploymentCreate, Deployment as DeploymentSchema
from apps.backend.src.services.deployment import DeploymentService

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


@router.post("", response_model=DeploymentSchema, status_code=status.HTTP_201_CREATED)
async def create_deployment(
    deployment_data: DeploymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new deployment."""
    require_permission(current_user.token_data, Permission.DEPLOYMENT_CREATE)
    
    # Verify project and workflow access
    result = await db.execute(
        select(Project).where(Project.id == deployment_data.project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", deployment_data.project_id)
    
    result = await db.execute(
        select(Workflow).where(Workflow.id == deployment_data.workflow_id, Workflow.project_id == deployment_data.project_id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise NotFoundError("Workflow", deployment_data.workflow_id)
    
    deployment_service = DeploymentService(db)
    deployment = await deployment_service.create_deployment(
        project_id=deployment_data.project_id,
        workflow_id=deployment_data.workflow_id,
        environment=deployment_data.environment,
        strategy=deployment_data.strategy,
        config=deployment_data.config,
        triggered_by=current_user.id,
    )
    
    return deployment


@router.get("", response_model=List[DeploymentSchema])
async def list_deployments(
    project_id: Optional[UUID] = None,
    environment: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List deployments with filtering."""
    require_permission(current_user.token_data, Permission.DEPLOYMENT_READ)
    
    query = select(Deployment).join(Project).where(Project.owner_id == current_user.id)
    
    if project_id:
        query = query.where(Deployment.project_id == project_id)
    
    if environment:
        query = query.where(Deployment.environment == environment)
    
    if status:
        query = query.where(Deployment.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Deployment.created_at.desc())
    
    result = await db.execute(query)
    deployments = result.scalars().all()
    
    return deployments


@router.get("/{deployment_id}", response_model=DeploymentSchema)
async def get_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a deployment by ID."""
    require_permission(current_user.token_data, Permission.DEPLOYMENT_READ)
    
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.artifacts))
        .join(Project)
        .where(Deployment.id == deployment_id, Project.owner_id == current_user.id)
    )
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("Deployment", deployment_id)
    
    return deployment


@router.post("/{deployment_id}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Execute a deployment."""
    require_permission(current_user.token_data, Permission.DEPLOYMENT_EXECUTE)
    
    result = await db.execute(
        select(Deployment)
        .join(Project)
        .where(Deployment.id == deployment_id, Project.owner_id == current_user.id)
    )
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("Deployment", deployment_id)
    
    if deployment.status == "running":
        raise HTTPException(status_code=400, detail="Deployment is already running")
    
    deployment_service = DeploymentService(db)
    await deployment_service.execute_deployment(deployment_id)
    
    return {"message": "Deployment started", "deployment_id": str(deployment_id)}


@router.post("/{deployment_id}/rollback", status_code=status.HTTP_200_OK)
async def rollback_deployment(
    deployment_id: UUID,
    target_version: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Rollback a deployment."""
    require_permission(current_user.token_data, Permission.DEPLOYMENT_ROLLBACK)
    
    result = await db.execute(
        select(Deployment)
        .join(Project)
        .where(Deployment.id == deployment_id, Project.owner_id == current_user.id)
    )
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("Deployment", deployment_id)
    
    deployment_service = DeploymentService(db)
    await deployment_service.rollback_deployment(deployment_id, target_version)
    
    return {"message": "Rollback started", "deployment_id": str(deployment_id)}


@router.get("/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get deployment logs."""
    require_permission(current_user.token_data, Permission.DEPLOYMENT_READ)
    
    result = await db.execute(
        select(Deployment)
        .join(Project)
        .where(Deployment.id == deployment_id, Project.owner_id == current_user.id)
    )
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("Deployment", deployment_id)
    
    return {
        "deployment_id": str(deployment_id),
        "logs": deployment.logs,
    }


@router.get("/{deployment_id}/status")
async def get_deployment_status(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get deployment status."""
    require_permission(current_user.token_data, Permission.DEPLOYMENT_READ)
    
    result = await db.execute(
        select(Deployment)
        .join(Project)
        .where(Deployment.id == deployment_id, Project.owner_id == current_user.id)
    )
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        raise NotFoundError("Deployment", deployment_id)
    
    return {
        "deployment_id": str(deployment_id),
        "status": deployment.status,
        "version": deployment.version,
        "environment": deployment.environment,
        "started_at": deployment.started_at.isoformat() if deployment.started_at else None,
        "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None,
        "error": deployment.error,
    }
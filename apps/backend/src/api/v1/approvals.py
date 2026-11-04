"""
Approval management endpoints for human-in-the-loop.
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
from apps.backend.src.models.entities import ApprovalRequest, User, Project, Workflow, Task
from apps.backend.src.models.schemas import ApprovalRequestCreate, ApprovalResponse as ApprovalResponseSchema, ApprovalRequest as ApprovalRequestSchema

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


@router.post("", response_model=ApprovalRequestSchema, status_code=status.HTTP_201_CREATED)
async def create_approval_request(
    approval_data: ApprovalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create an approval request."""
    require_permission(current_user.token_data, Permission.WORKFLOW_CREATE)
    
    # Verify workflow access
    result = await db.execute(
        select(Workflow)
        .join(Project)
        .where(Workflow.id == approval_data.workflow_id, Project.owner_id == current_user.id)
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise NotFoundError("Workflow", approval_data.workflow_id)
    
    # Verify task exists
    result = await db.execute(
        select(Task).where(Task.id == approval_data.task_id, Task.workflow_id == approval_data.workflow_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", approval_data.task_id)
    
    approval = ApprovalRequest(
        workflow_id=approval_data.workflow_id,
        task_id=approval_data.task_id,
        title=approval_data.title,
        description=approval_data.description,
        options=approval_data.options,
        requested_by=approval_data.requested_by,
        expires_at=approval_data.expires_at,
    )
    
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    
    # Notify via websocket
    from apps.backend.src.api.v1.websocket import manager
    await manager.broadcast_to_workflow(
        approval_data.workflow_id,
        {
            "type": "approval_requested",
            "approval_id": str(approval.id),
            "title": approval.title,
        }
    )
    
    return approval


@router.get("", response_model=List[ApprovalRequestSchema])
async def list_approval_requests(
    workflow_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List approval requests."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    query = select(ApprovalRequest).join(Workflow).join(Project).where(Project.owner_id == current_user.id)
    
    if workflow_id:
        query = query.where(ApprovalRequest.workflow_id == workflow_id)
    
    if status:
        query = query.where(ApprovalRequest.status == status)
    
    query = query.offset(skip).limit(limit).order_by(ApprovalRequest.created_at.desc())
    
    result = await db.execute(query)
    approvals = result.scalars().all()
    
    return approvals


@router.get("/{approval_id}", response_model=ApprovalRequestSchema)
async def get_approval_request(
    approval_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get an approval request by ID."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    result = await db.execute(
        select(ApprovalRequest)
        .options(selectinload(ApprovalRequest.workflow).selectinload(Workflow.project))
        .where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    
    if not approval:
        raise NotFoundError("ApprovalRequest", approval_id)
    
    # Verify project access
    if approval.workflow.project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return approval


@router.post("/{approval_id}/respond", response_model=ApprovalRequestSchema)
async def respond_to_approval(
    approval_id: UUID,
    response: ApprovalResponseSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Respond to an approval request."""
    require_permission(current_user.token_data, Permission.WORKFLOW_APPROVE)
    
    result = await db.execute(
        select(ApprovalRequest)
        .options(selectinload(ApprovalRequest.workflow).selectinload(Workflow.project))
        .where(ApprovalRequest.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    
    if not approval:
        raise NotFoundError("ApprovalRequest", approval_id)
    
    # Verify project access
    if approval.workflow.project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval request already responded")
    
    approval.status = "approved" if response.approved else "rejected"
    approval.selected_option = response.selected_option
    approval.comments = response.comments
    approval.decided_by = current_user.id
    approval.decided_at = __import__("datetime").datetime.utcnow()
    
    await db.commit()
    await db.refresh(approval)
    
    # Notify via websocket
    from apps.backend.src.api.v1.websocket import manager
    await manager.broadcast_to_workflow(
        approval.workflow_id,
        {
            "type": "approval_responded",
            "approval_id": str(approval_id),
            "approved": response.approved,
            "decided_by": str(current_user.id),
        }
    )
    
    return approval


@router.get("/pending/count")
async def get_pending_approvals_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get count of pending approval requests."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    result = await db.execute(
        select(ApprovalRequest)
        .join(Workflow)
        .join(Project)
        .where(Project.owner_id == current_user.id, ApprovalRequest.status == "pending")
    )
    count = len(result.scalars().all())
    
    return {"pending_count": count}
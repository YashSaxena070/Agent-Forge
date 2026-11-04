"""
Agent management endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.core.database import get_db_session
from apps.backend.src.core.security import (
    Permission,
    require_permission,
    verify_token,
)
from apps.backend.src.core.exceptions import NotFoundError
from apps.backend.src.models.entities import User, AgentExecution
from services.shared.schemas import AgentRole, TaskStatus
from apps.backend.src.agents.base import AgentRegistry

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


@router.get("", response_model=List[dict])
async def list_agents(
    current_user: User = Depends(get_current_user),
):
    """List all available agents."""
    require_permission(current_user.token_data, Permission.AGENT_READ)
    
    agents = AgentRegistry.get_all_agents()
    
    return [
        {
            "role": agent.role.value,
            "name": agent.name,
            "description": agent.description,
            "capabilities": agent.capabilities,
            "tools": [tool.name for tool in agent.tools],
        }
        for agent in agents
    ]


@router.get("/{role}", response_model=dict)
async def get_agent(
    role: AgentRole,
    current_user: User = Depends(get_current_user),
):
    """Get agent details by role."""
    require_permission(current_user.token_data, Permission.AGENT_READ)
    
    agent = AgentRegistry.get_agent(role)
    
    if not agent:
        raise NotFoundError("Agent", role.value)
    
    return {
        "role": agent.role.value,
        "name": agent.name,
        "description": agent.description,
        "capabilities": agent.capabilities,
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in agent.tools
        ],
        "prompt_template": agent.prompt_template,
    }


@router.get("/{role}/executions", response_model=List[dict])
async def get_agent_executions(
    role: AgentRole,
    task_id: Optional[UUID] = None,
    status: Optional[TaskStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get agent execution history."""
    require_permission(current_user.token_data, Permission.AGENT_READ)
    
    query = select(AgentExecution).where(AgentExecution.agent_role == role)
    
    if task_id:
        query = query.where(AgentExecution.task_id == task_id)
    
    if status:
        query = query.where(AgentExecution.status == status)
    
    query = query.offset(skip).limit(limit).order_by(AgentExecution.started_at.desc())
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return [
        {
            "id": str(execution.id),
            "task_id": str(execution.task_id),
            "status": execution.status,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration_seconds": execution.duration_seconds,
            "tokens_used": execution.tokens_used,
            "cost_usd": execution.cost_usd,
            "error": execution.error,
        }
        for execution in executions
    ]


@router.post("/{role}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_agent(
    role: AgentRole,
    task_id: UUID,
    input_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Execute an agent directly (for testing)."""
    require_permission(current_user.token_data, Permission.AGENT_EXECUTE)
    
    from apps.backend.src.agents.base import AgentRegistry
    from apps.backend.src.models.entities import Task
    
    # Verify task exists and user has access
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundError("Task", task_id)
    
    agent = AgentRegistry.get_agent(role)
    
    if not agent:
        raise NotFoundError("Agent", role.value)
    
    # Execute agent asynchronously
    import asyncio
    asyncio.create_task(agent.execute(task_id, input_data, db))
    
    return {"message": "Agent execution started", "task_id": str(task_id), "agent": role.value}
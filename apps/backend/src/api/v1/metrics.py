"""
Metrics and observability endpoints.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.core.database import get_db_session
from apps.backend.src.core.security import (
    Permission,
    require_permission,
    verify_token,
)
from apps.backend.src.models.entities import User, Project, Workflow, Task, AgentExecution, Deployment
from apps.backend.src.core.telemetry import get_meter

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


@router.get("/workflows")
async def get_workflow_metrics(
    project_id: Optional[UUID] = None,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get workflow execution metrics."""
    require_permission(current_user.token_data, Permission.ADMIN_METRICS)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(Workflow).join(Project).where(
        Project.owner_id == current_user.id,
        Workflow.created_at >= since,
    )
    
    if project_id:
        query = query.where(Workflow.project_id == project_id)
    
    result = await db.execute(query)
    workflows = result.scalars().all()
    
    total = len(workflows)
    completed = len([w for w in workflows if w.status == "completed"])
    failed = len([w for w in workflows if w.status == "failed"])
    running = len([w for w in workflows if w.status == "running"])
    
    durations = [w.duration_seconds for w in workflows if w.duration_seconds]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    return {
        "period_days": days,
        "total_workflows": total,
        "completed": completed,
        "failed": failed,
        "running": running,
        "success_rate": completed / total if total > 0 else 0,
        "avg_duration_seconds": avg_duration,
        "by_phase": {
            phase: len([w for w in workflows if w.current_phase == phase])
            for phase in ["planning", "design", "implementation", "review", "testing", "deployment", "monitoring"]
        },
    }


@router.get("/agents")
async def get_agent_metrics(
    project_id: Optional[UUID] = None,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get agent execution metrics."""
    require_permission(current_user.token_data, Permission.ADMIN_METRICS)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(AgentExecution).where(AgentExecution.started_at >= since)
    
    if project_id:
        # Join through task -> workflow -> project
        query = query.join(Task).join(Workflow).join(Project).where(Project.id == project_id)
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    by_role = {}
    for exec in executions:
        role = exec.agent_role
        if role not in by_role:
            by_role[role] = {"total": 0, "success": 0, "failed": 0, "avg_duration": 0, "total_tokens": 0, "total_cost": 0}
        by_role[role]["total"] += 1
        if exec.status == "completed":
            by_role[role]["success"] += 1
        elif exec.status == "failed":
            by_role[role]["failed"] += 1
        if exec.duration_seconds:
            by_role[role]["avg_duration"] += exec.duration_seconds
        by_role[role]["total_tokens"] += exec.tokens_used or 0
        by_role[role]["total_cost"] += exec.cost_usd or 0
    
    for role in by_role:
        if by_role[role]["total"] > 0:
            by_role[role]["avg_duration"] /= by_role[role]["total"]
            by_role[role]["success_rate"] = by_role[role]["success"] / by_role[role]["total"]
    
    return {
        "period_days": days,
        "by_role": by_role,
        "total_executions": len(executions),
        "total_tokens": sum(e.tokens_used or 0 for e in executions),
        "total_cost_usd": sum(e.cost_usd or 0 for e in executions),
    }


@router.get("/tasks")
async def get_task_metrics(
    project_id: Optional[UUID] = None,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get task execution metrics."""
    require_permission(current_user.token_data, Permission.ADMIN_METRICS)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(Task).join(Project).where(
        Project.owner_id == current_user.id,
        Task.created_at >= since,
    )
    
    if project_id:
        query = query.where(Task.project_id == project_id)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    by_status = {}
    by_role = {}
    
    for task in tasks:
        # By status
        status = task.status
        by_status[status] = by_status.get(status, 0) + 1
        
        # By role
        role = task.role
        if role not in by_role:
            by_role[role] = {"total": 0, "completed": 0, "failed": 0}
        by_role[role]["total"] += 1
        if task.status == "completed":
            by_role[role]["completed"] += 1
        elif task.status == "failed":
            by_role[role]["failed"] += 1
    
    return {
        "period_days": days,
        "total_tasks": len(tasks),
        "by_status": by_status,
        "by_role": by_role,
    }


@router.get("/deployments")
async def get_deployment_metrics(
    project_id: Optional[UUID] = None,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get deployment metrics."""
    require_permission(current_user.token_data, Permission.ADMIN_METRICS)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(Deployment).join(Project).where(
        Project.owner_id == current_user.id,
        Deployment.created_at >= since,
    )
    
    if project_id:
        query = query.where(Deployment.project_id == project_id)
    
    result = await db.execute(query)
    deployments = result.scalars().all()
    
    total = len(deployments)
    successful = len([d for d in deployments if d.status == "completed"])
    failed = len([d for d in deployments if d.status == "failed"])
    rolled_back = len([d for d in deployments if d.status == "rolled_back"])
    
    durations = [d.duration_seconds for d in deployments if d.duration_seconds]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    return {
        "period_days": days,
        "total_deployments": total,
        "successful": successful,
        "failed": failed,
        "rolled_back": rolled_back,
        "success_rate": successful / total if total > 0 else 0,
        "avg_duration_seconds": avg_duration,
        "by_environment": {
            env: len([d for d in deployments if d.environment == env])
            for env in ["dev", "staging", "prod"]
        },
    }


@router.get("/costs")
async def get_cost_metrics(
    project_id: Optional[UUID] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get LLM cost metrics."""
    require_permission(current_user.token_data, Permission.ADMIN_METRICS)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(AgentExecution).where(AgentExecution.started_at >= since)
    
    if project_id:
        query = query.join(Task).join(Workflow).join(Project).where(Project.id == project_id)
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    by_provider = {}
    by_model = {}
    daily_costs = {}
    
    for exec in executions:
        provider = exec.llm_provider or "unknown"
        model = exec.llm_model or "unknown"
        cost = exec.cost_usd or 0
        date = exec.started_at.date().isoformat() if exec.started_at else "unknown"
        
        by_provider[provider] = by_provider.get(provider, 0) + cost
        by_model[model] = by_model.get(model, 0) + cost
        daily_costs[date] = daily_costs.get(date, 0) + cost
    
    total_cost = sum(by_provider.values())
    
    return {
        "period_days": days,
        "total_cost_usd": total_cost,
        "by_provider": by_provider,
        "by_model": by_model,
        "daily_costs": daily_costs,
    }


@router.get("/system")
async def get_system_metrics(
    current_user: User = Depends(get_current_user),
):
    """Get system-level metrics from Prometheus."""
    require_permission(current_user.token_data, Permission.ADMIN_METRICS)
    
    # These would be scraped from Prometheus in production
    # For now, return placeholder structure
    return {
        "cpu_usage_percent": 0,
        "memory_usage_percent": 0,
        "disk_usage_percent": 0,
        "network_io_mbps": 0,
        "active_connections": 0,
        "queue_depth": 0,
    }
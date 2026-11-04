"""
Memory management endpoints.
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
from apps.backend.src.core.exceptions import NotFoundError, MemoryError
from apps.backend.src.models.entities import User, Project
from apps.backend.src.memory.manager import MemoryManager

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


@router.post("/short-term", status_code=status.HTTP_201_CREATED)
async def store_short_term_memory(
    project_id: UUID,
    key: str,
    value: dict,
    ttl_hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Store short-term memory."""
    require_permission(current_user.token_data, Permission.WORKFLOW_CREATE)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        memory_manager = MemoryManager()
        await memory_manager.short_term.store(
            project_id=project_id,
            key=key,
            value=value,
            ttl_hours=ttl_hours,
        )
        return {"message": "Short-term memory stored", "key": key}
    except Exception as e:
        raise MemoryError(f"Storage failed: {str(e)}")


@router.get("/short-term/{project_id}/{key}")
async def get_short_term_memory(
    project_id: UUID,
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get short-term memory."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        memory_manager = MemoryManager()
        value = await memory_manager.short_term.get(project_id, key)
        
        if value is None:
            raise NotFoundError("Memory key", key)
        
        return {"key": key, "value": value}
    except NotFoundError:
        raise
    except Exception as e:
        raise MemoryError(f"Retrieval failed: {str(e)}")


@router.delete("/short-term/{project_id}/{key}", status_code=status.HTTP_200_OK)
async def delete_short_term_memory(
    project_id: UUID,
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete short-term memory."""
    require_permission(current_user.token_data, Permission.WORKFLOW_UPDATE)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        memory_manager = MemoryManager()
        await memory_manager.short_term.delete(project_id, key)
        return {"message": "Short-term memory deleted", "key": key}
    except Exception as e:
        raise MemoryError(f"Deletion failed: {str(e)}")


@router.post("/long-term", status_code=status.HTTP_201_CREATED)
async def store_long_term_memory(
    project_id: UUID,
    key: str,
    value: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Store long-term memory."""
    require_permission(current_user.token_data, Permission.WORKFLOW_CREATE)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        memory_manager = MemoryManager()
        await memory_manager.long_term.store(
            project_id=project_id,
            key=key,
            value=value,
        )
        return {"message": "Long-term memory stored", "key": key}
    except Exception as e:
        raise MemoryError(f"Storage failed: {str(e)}")


@router.get("/long-term/{project_id}/{key}")
async def get_long_term_memory(
    project_id: UUID,
    key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get long-term memory."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        memory_manager = MemoryManager()
        value = await memory_manager.long_term.get(project_id, key)
        
        if value is None:
            raise NotFoundError("Memory key", key)
        
        return {"key": key, "value": value}
    except NotFoundError:
        raise
    except Exception as e:
        raise MemoryError(f"Retrieval failed: {str(e)}")


@router.post("/semantic/search", status_code=status.HTTP_200_OK)
async def search_semantic_memory(
    project_id: UUID,
    query: str,
    top_k: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Search semantic memory."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        memory_manager = MemoryManager()
        results = await memory_manager.semantic.search(
            project_id=project_id,
            query=query,
            top_k=top_k,
        )
        return {"query": query, "results": results}
    except Exception as e:
        raise MemoryError(f"Search failed: {str(e)}")


@router.post("/relationship/query", status_code=status.HTTP_200_OK)
async def query_relationship_memory(
    project_id: UUID,
    entity: str,
    relationship_type: Optional[str] = None,
    max_depth: int = 3,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Query relationship memory."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        memory_manager = MemoryManager()
        results = await memory_manager.relationship.query(
            project_id=project_id,
            entity=entity,
            relationship_type=relationship_type,
            max_depth=max_depth,
        )
        return {"entity": entity, "relationship_type": relationship_type, "results": results}
    except Exception as e:
        raise MemoryError(f"Query failed: {str(e)}")


@router.get("/project/{project_id}/stats")
async def get_project_memory_stats(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get memory statistics for a project."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        memory_manager = MemoryManager()
        stats = await memory_manager.get_project_stats(project_id)
        return {"project_id": str(project_id), "stats": stats}
    except Exception as e:
        raise MemoryError(f"Stats retrieval failed: {str(e)}")
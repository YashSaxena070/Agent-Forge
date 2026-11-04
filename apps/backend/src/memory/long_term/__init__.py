"""
Long-term memory using PostgreSQL.
"""
import json
from typing import Any, Dict, Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.core.database import db_manager
from apps.backend.src.models.entities import LongTermMemory
from apps.backend.src.core.exceptions import MemoryError


class LongTermMemoryStore:
    """Long-term persistent memory using PostgreSQL."""
    
    async def store(
        self,
        project_id: UUID,
        key: str,
        value: Dict[str, Any],
        metadata: Dict[str, Any] = None,
    ) -> LongTermMemory:
        """Store or update long-term memory."""
        async with db_manager.session() as session:
            # Check if exists
            result = await session.execute(
                select(LongTermMemory).where(
                    LongTermMemory.project_id == project_id,
                    LongTermMemory.key == key,
                )
            )
            memory = result.scalar_one_or_none()
            
            if memory:
                memory.value = value
                memory.metadata = metadata or {}
                memory.updated_at = datetime.utcnow()
                memory.version += 1
            else:
                memory = LongTermMemory(
                    project_id=project_id,
                    key=key,
                    value=value,
                    metadata=metadata or {},
                )
                session.add(memory)
            
            await session.commit()
            await session.refresh(memory)
            
            return memory
    
    async def get(
        self,
        project_id: UUID,
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """Get long-term memory by key."""
        async with db_manager.session() as session:
            result = await session.execute(
                select(LongTermMemory).where(
                    LongTermMemory.project_id == project_id,
                    LongTermMemory.key == key,
                )
            )
            memory = result.scalar_one_or_none()
            
            if memory:
                return memory.value
            return None
    
    async def get_with_metadata(
        self,
        project_id: UUID,
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """Get long-term memory with metadata."""
        async with db_manager.session() as session:
            result = await session.execute(
                select(LongTermMemory).where(
                    LongTermMemory.project_id == project_id,
                    LongTermMemory.key == key,
                )
            )
            memory = result.scalar_one_or_none()
            
            if memory:
                return {
                    "key": memory.key,
                    "value": memory.value,
                    "metadata": memory.metadata,
                    "version": memory.version,
                    "created_at": memory.created_at.isoformat(),
                    "updated_at": memory.updated_at.isoformat(),
                }
            return None
    
    async def delete(self, project_id: UUID, key: str) -> bool:
        """Delete long-term memory."""
        async with db_manager.session() as session:
            result = await session.execute(
                delete(LongTermMemory).where(
                    LongTermMemory.project_id == project_id,
                    LongTermMemory.key == key,
                )
            )
            await session.commit()
            return result.rowcount > 0
    
    async def list_keys(
        self,
        project_id: UUID,
        prefix: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> List[str]:
        """List all keys for a project."""
        async with db_manager.session() as session:
            query = select(LongTermMemory.key).where(
                LongTermMemory.project_id == project_id,
            )
            
            if prefix:
                query = query.where(LongTermMemory.key.like(f"{prefix}%"))
            
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            return [row[0] for row in result.fetchall()]
    
    async def search(
        self,
        project_id: UUID,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search long-term memory by content (simple text search)."""
        async with db_manager.session() as session:
            # Simple ILIKE search on value
            result = await session.execute(
                select(LongTermMemory).where(
                    LongTermMemory.project_id == project_id,
                    LongTermMemory.value.cast(str).ilike(f"%{query}%"),
                ).limit(limit)
            )
            memories = result.scalars().all()
            
            return [
                {
                    "key": m.key,
                    "value": m.value,
                    "metadata": m.metadata,
                }
                for m in memories
            ]


# Global instance
_long_term_memory: Optional[LongTermMemoryStore] = None


def get_long_term_memory() -> LongTermMemoryStore:
    """Get or create long-term memory instance."""
    global _long_term_memory
    if _long_term_memory is None:
        _long_term_memory = LongTermMemoryStore()
    return _long_term_memory
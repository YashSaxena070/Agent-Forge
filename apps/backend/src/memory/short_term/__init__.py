"""
Short-term memory using Redis.
"""
import json
from typing import Any, Dict, Optional
from uuid import UUID

import redis.asyncio as redis

from apps.backend.src.core.config import settings
from apps.backend.src.core.exceptions import MemoryError


class ShortTermMemory:
    """Short-term memory with TTL using Redis."""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.default_ttl = settings.SHORT_TERM_TTL_HOURS * 3600
    
    async def initialize(self):
        """Initialize Redis connection."""
        self.client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await self.client.ping()
    
    def _make_key(self, project_id: UUID, key: str) -> str:
        """Create Redis key with project prefix."""
        return f"agentforge:stm:{project_id}:{key}"
    
    async def store(
        self,
        project_id: UUID,
        key: str,
        value: Dict[str, Any],
        ttl_hours: Optional[int] = None,
    ) -> bool:
        """Store value with TTL."""
        if not self.client:
            await self.initialize()
        
        redis_key = self._make_key(project_id, key)
        ttl = (ttl_hours or self.default_ttl // 3600) * 3600
        
        try:
            await self.client.setex(
                redis_key,
                ttl,
                json.dumps(value, default=str),
            )
            return True
        except Exception as e:
            raise MemoryError(f"Failed to store: {str(e)}", memory_type="short_term", operation="store")
    
    async def get(self, project_id: UUID, key: str) -> Optional[Dict[str, Any]]:
        """Get value by key."""
        if not self.client:
            await self.initialize()
        
        redis_key = self._make_key(project_id, key)
        
        try:
            value = await self.client.get(redis_key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            raise MemoryError(f"Failed to get: {str(e)}", memory_type="short_term", operation="get")
    
    async def delete(self, project_id: UUID, key: str) -> bool:
        """Delete value by key."""
        if not self.client:
            await self.initialize()
        
        redis_key = self._make_key(project_id, key)
        
        try:
            result = await self.client.delete(redis_key)
            return result > 0
        except Exception as e:
            raise MemoryError(f"Failed to delete: {str(e)}", memory_type="short_term", operation="delete")
    
    async def exists(self, project_id: UUID, key: str) -> bool:
        """Check if key exists."""
        if not self.client:
            await self.initialize()
        
        redis_key = self._make_key(project_id, key)
        
        try:
            return await self.client.exists(redis_key) > 0
        except Exception:
            return False
    
    async def get_ttl(self, project_id: UUID, key: str) -> int:
        """Get remaining TTL for key."""
        if not self.client:
            await self.initialize()
        
        redis_key = self._make_key(project_id, key)
        
        try:
            ttl = await self.client.ttl(redis_key)
            return max(0, ttl)
        except Exception:
            return -1
    
    async def extend_ttl(self, project_id: UUID, key: str, ttl_hours: int) -> bool:
        """Extend TTL for key."""
        if not self.client:
            await self.initialize()
        
        redis_key = self._make_key(project_id, key)
        ttl = ttl_hours * 3600
        
        try:
            return await self.client.expire(redis_key, ttl)
        except Exception:
            return False
    
    async def get_all_keys(self, project_id: UUID, pattern: str = "*") -> list:
        """Get all keys for a project."""
        if not self.client:
            await self.initialize()
        
        redis_pattern = self._make_key(project_id, pattern)
        
        try:
            keys = []
            async for key in self.client.scan_iter(match=redis_pattern):
                keys.append(key.replace(f"agentforge:stm:{project_id}:", ""))
            return keys
        except Exception:
            return []


# Global instance
_short_term_memory: Optional[ShortTermMemory] = None


def get_short_term_memory() -> ShortTermMemory:
    """Get or create short-term memory instance."""
    global _short_term_memory
    if _short_term_memory is None:
        _short_term_memory = ShortTermMemory()
    return _short_term_memory
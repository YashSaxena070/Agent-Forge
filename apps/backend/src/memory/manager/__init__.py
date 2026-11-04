"""
Memory manager coordinating all memory systems.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from apps.backend.src.memory.short_term import get_short_term_memory
from apps.backend.src.memory.long_term import get_long_term_memory
from apps.backend.src.memory.semantic import get_semantic_memory
from apps.backend.src.memory.relationship import get_relationship_memory
from apps.backend.src.core.exceptions import MemoryError


class MemoryManager:
    """Unified memory manager for all memory systems."""
    
    def __init__(self):
        self.short_term = get_short_term_memory()
        self.long_term = get_long_term_memory()
        self.semantic = get_semantic_memory()
        self.relationship = get_relationship_memory()
    
    async def initialize(self):
        """Initialize all memory systems."""
        await self.short_term.initialize()
        await self.semantic.vector_store.initialize()
        await self.relationship.graph_store.initialize()
    
    async def store_execution_context(
        self,
        project_id: UUID,
        workflow_id: UUID,
        context: Dict[str, Any],
    ) -> bool:
        """Store execution context in short-term memory."""
        key = f"workflow:{workflow_id}:context"
        return await self.short_term.store(project_id, key, context, ttl_hours=24)
    
    async def get_execution_context(
        self,
        project_id: UUID,
        workflow_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """Get execution context from short-term memory."""
        key = f"workflow:{workflow_id}:context"
        return await self.short_term.get(project_id, key)
    
    async def store_project_knowledge(
        self,
        project_id: UUID,
        key: str,
        value: Dict[str, Any],
        memory_type: str = "long_term",
    ) -> bool:
        """Store project knowledge in appropriate memory."""
        if memory_type == "short_term":
            return await self.short_term.store(project_id, key, value)
        elif memory_type == "long_term":
            await self.long_term.store(project_id, key, value)
            return True
        elif memory_type == "semantic":
            await self.semantic.store(project_id, key, str(value))
            return True
        return False
    
    async def get_project_knowledge(
        self,
        project_id: UUID,
        key: str,
        memory_type: str = "long_term",
    ) -> Optional[Dict[str, Any]]:
        """Get project knowledge from appropriate memory."""
        if memory_type == "short_term":
            return await self.short_term.get(project_id, key)
        elif memory_type == "long_term":
            return await self.long_term.get(project_id, key)
        elif memory_type == "semantic":
            return await self.semantic.get_concept(project_id, key)
        return None
    
    async def search_knowledge(
        self,
        project_id: UUID,
        query: str,
        memory_types: List[str] = None,
        top_k: int = 10,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search across all memory systems."""
        memory_types = memory_types or ["semantic", "relationship"]
        results = {}
        
        if "semantic" in memory_types:
            results["semantic"] = await self.semantic.search(project_id, query, top_k)
        
        if "relationship" in memory_types:
            results["relationship"] = await self.relationship.query(project_id, query)
        
        if "long_term" in memory_types:
            results["long_term"] = await self.long_term.search(project_id, query, top_k)
        
        return results
    
    async def add_relationship(
        self,
        project_id: UUID,
        source: str,
        target: str,
        relationship_type: str,
        description: str = "",
    ) -> bool:
        """Add entity relationship."""
        return await self.relationship.add_relationship(
            project_id, source, target, relationship_type, description
        )
    
    async def get_entity_relationships(
        self,
        project_id: UUID,
        entity: str,
    ) -> List[Dict[str, Any]]:
        """Get relationships for an entity."""
        return await self.relationship.query(project_id, entity)
    
    async def get_project_stats(self, project_id: UUID) -> Dict[str, Any]:
        """Get memory statistics for a project."""
        return {
            "short_term_keys": len(await self.short_term.get_all_keys(project_id)),
            "long_term_keys": len(await self.long_term.list_keys(project_id)),
            "semantic_concepts": len(await self.semantic.list_concepts(project_id)),
            "relationship_stats": await self.relationship.graph_store.get_project_stats(project_id),
        }
    
    async def cleanup_expired(self, project_id: UUID) -> int:
        """Clean up expired short-term memory (Redis handles TTL automatically)."""
        # Redis handles TTL automatically, but we can clean up empty keys
        return 0


# Global instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
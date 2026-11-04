"""
Semantic memory using Qdrant for vector similarity.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from apps.backend.src.rag.vector.store import get_vector_store
from apps.backend.src.core.exceptions import MemoryError


class SemanticMemory:
    """Semantic memory for concept-based retrieval."""
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.collection_prefix = "agentforge_semantic_"
        self.max_entries = 10000
    
    def _get_collection_name(self, project_id: UUID) -> str:
        return f"{self.collection_prefix}{project_id.hex}"
    
    async def store(
        self,
        project_id: UUID,
        concept: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Store a semantic concept."""
        import uuid
        
        doc_id = str(uuid.uuid4())
        
        document = {
            "id": doc_id,
            "content": content,
            "title": concept,
            "type": "semantic_concept",
            "metadata": {
                "concept": concept,
                **(metadata or {}),
            },
        }
        
        try:
            await self.vector_store.add_documents(project_id, [document])
            return doc_id
        except Exception as e:
            raise MemoryError(f"Failed to store semantic memory: {str(e)}", memory_type="semantic", operation="store")
    
    async def search(
        self,
        project_id: UUID,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for semantically similar concepts."""
        try:
            results = await self.vector_store.search(
                project_id=project_id,
                query=query,
                top_k=top_k,
                filters={"document_type": "semantic_concept"},
            )
            
            # Filter by threshold
            filtered = [r for r in results if r.get("score", 0) >= threshold]
            
            return filtered
        except Exception as e:
            raise MemoryError(f"Failed to search semantic memory: {str(e)}", memory_type="semantic", operation="search")
    
    async def get_concept(
        self,
        project_id: UUID,
        concept: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific concept by exact match."""
        results = await self.search(project_id, concept, top_k=1, threshold=0.95)
        
        if results:
            return results[0]
        return None
    
    async def delete_concept(
        self,
        project_id: UUID,
        concept: str,
    ) -> bool:
        """Delete a concept (by marking as deleted)."""
        # In Qdrant, we'd need to delete by ID
        # For now, store a tombstone
        await self.store(project_id, concept, "", {"deleted": True, "original_concept": concept})
        return True
    
    async def list_concepts(
        self,
        project_id: UUID,
        limit: int = 100,
    ) -> List[str]:
        """List all concepts (approximate via search)."""
        # This is a limitation - would need a separate index
        results = await self.search(project_id, "", top_k=limit, threshold=0.0)
        return [r.get("title", "") for r in results]


# Global instance
_semantic_memory: Optional[SemanticMemory] = None


def get_semantic_memory() -> SemanticMemory:
    """Get or create semantic memory instance."""
    global _semantic_memory
    if _semantic_memory is None:
        _semantic_memory = SemanticMemory()
    return _semantic_memory
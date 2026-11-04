"""
Vector store for semantic search using Qdrant.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
    PayloadSchemaType,
)

from apps.backend.src.core.config import settings
from apps.backend.src.core.telemetry import record_rag_metrics
from apps.backend.src.core.exceptions import RAGError


class VectorStore:
    """Vector store for semantic document retrieval."""
    
    def __init__(self):
        self.client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        self.collection_prefix = "agentforge_"
    
    async def initialize(self):
        """Initialize the client."""
        # Test connection
        await self.client.get_collections()
    
    def _get_collection_name(self, project_id: UUID) -> str:
        """Get collection name for project."""
        return f"{self.collection_prefix}{project_id.hex}"
    
    async def create_collection(self, project_id: UUID, vector_size: int = 1536) -> bool:
        """Create collection for project if not exists."""
        collection_name = self._get_collection_name(project_id)
        
        try:
            collections = await self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)
            
            if not exists:
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE,
                    ),
                )
                
                # Create payload indexes for filtering
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="project_id",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="document_type",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
                await self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="source",
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            
            return True
        except Exception as e:
            raise RAGError(f"Failed to create collection: {str(e)}", stage="create_collection")
    
    async def add_documents(
        self,
        project_id: UUID,
        documents: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
    ) -> int:
        """Add documents to vector store."""
        collection_name = self._get_collection_name(project_id)
        
        await self.create_collection(project_id)
        
        points = []
        for i, doc in enumerate(documents):
            # Generate embedding (placeholder - would use actual embedding model)
            embedding = await self._generate_embedding(doc.get("content", ""))
            
            point_id = str(UUID(bytes=bytes.fromhex(doc.get("id", "")[:32]))) if doc.get("id") else str(uuid4())
            
            payload = {
                "project_id": str(project_id),
                "content": doc.get("content", ""),
                "title": doc.get("title", ""),
                "document_type": doc.get("type", "document"),
                "source": metadata.get("source", "unknown") if metadata else "unknown",
                "metadata": {**doc.get("metadata", {}), **(metadata or {})},
            }
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            ))
        
        try:
            await self.client.upsert(
                collection_name=collection_name,
                points=points,
            )
            return len(points)
        except Exception as e:
            raise RAGError(f"Failed to add documents: {str(e)}", stage="add_documents")
    
    async def search(
        self,
        project_id: UUID,
        query: str,
        top_k: int = 10,
        filters: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        collection_name = self._get_collection_name(project_id)
        
        query_vector = await self._generate_embedding(query)
        
        # Build filter
        filter_conditions = []
        if filters:
            for key, value in filters.items():
                filter_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
        
        search_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
            )
            
            duration = asyncio.get_event_loop().time() - start_time
            record_rag_metrics(query, duration, len(results), "vector")
            
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "content": hit.payload.get("content", ""),
                    "title": hit.payload.get("title", ""),
                    "document_type": hit.payload.get("document_type", ""),
                    "source": hit.payload.get("source", ""),
                    "metadata": hit.payload.get("metadata", {}),
                }
                for hit in results
            ]
        except Exception as e:
            raise RAGError(f"Search failed: {str(e)}", stage="search", query=query)
    
    async def delete_project(self, project_id: UUID) -> bool:
        """Delete all vectors for a project."""
        collection_name = self._get_collection_name(project_id)
        
        try:
            await self.client.delete_collection(collection_name)
            return True
        except Exception as e:
            raise RAGError(f"Failed to delete project: {str(e)}", stage="delete_project")
    
    async def get_project_stats(self, project_id: UUID) -> Dict[str, Any]:
        """Get statistics for a project's vector collection."""
        collection_name = self._get_collection_name(project_id)
        
        try:
            info = await self.client.get_collection(collection_name)
            return {
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "status": info.status,
            }
        except Exception:
            return {"vectors_count": 0, "status": "not_found"}
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        # Placeholder - would integrate with actual embedding model
        # For now, return a random vector
        import random
        random.seed(hash(text) % (2**32))
        return [random.uniform(-1, 1) for _ in range(1536)]
    
    async def close(self):
        """Close the client."""
        await self.client.close()


# Global instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
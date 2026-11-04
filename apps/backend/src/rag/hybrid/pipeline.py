"""
Hybrid RAG pipeline combining vector and graph search.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from apps.backend.src.rag.vector.store import get_vector_store
from apps.backend.src.rag.graph.store import get_graph_store
from apps.backend.src.rag.reranker import get_reranker
from apps.backend.src.core.telemetry import record_rag_metrics
from apps.backend.src.core.exceptions import RAGError
from apps.backend.src.models.schemas import RAGQuery, RAGResponse, RAGResult


class HybridRAGPipeline:
    """Hybrid RAG pipeline combining vector and graph search."""
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.graph_store = get_graph_store()
        self.reranker = get_reranker()
    
    async def query(
        self,
        query: str,
        project_id: Optional[UUID] = None,
        top_k: int = 10,
        rerank_top_k: int = 5,
        filters: Dict[str, Any] = None,
    ) -> RAGResponse:
        """Execute hybrid query."""
        import time
        start_time = time.time()
        
        try:
            # Parallel search in vector and graph stores
            vector_results = []
            graph_results = []
            
            if project_id:
                vector_results, graph_results = await asyncio.gather(
                    self._search_vector(project_id, query, top_k, filters),
                    self._search_graph(project_id, query, top_k, filters),
                    return_exceptions=True,
                )
                
                # Handle exceptions
                if isinstance(vector_results, Exception):
                    vector_results = []
                if isinstance(graph_results, Exception):
                    graph_results = []
            
            # Merge results
            merged_results = self._merge_results(vector_results, graph_results)
            
            # Rerank
            reranked_results = await self.reranker.rerank(
                query=query,
                results=merged_results,
                top_k=rerank_top_k,
            )
            
            # Compress context
            compressed_context = self._compress_context(reranked_results)
            
            duration = time.time() - start_time
            record_rag_metrics(query, duration, len(reranked_results), "hybrid")
            
            return RAGResponse(
                query=query,
                results=reranked_results,
                compressed_context=compressed_context,
                total_results=len(merged_results),
                search_time_ms=duration * 1000,
            )
            
        except Exception as e:
            raise RAGError(f"Hybrid query failed: {str(e)}", stage="query", query=query)
    
    async def _search_vector(
        self,
        project_id: UUID,
        query: str,
        top_k: int,
        filters: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """Search vector store."""
        results = await self.vector_store.search(
            project_id=project_id,
            query=query,
            top_k=top_k,
            filters=filters,
        )
        
        for r in results:
            r["source"] = "vector"
        
        return results
    
    async def _search_graph(
        self,
        project_id: UUID,
        query: str,
        top_k: int,
        filters: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """Search graph store."""
        results = await self.graph_store.search(
            project_id=project_id,
            query=query,
            top_k=top_k,
            filters=filters,
        )
        
        for r in results:
            r["source"] = "graph"
        
        return results
    
    def _merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge and deduplicate results from both sources."""
        # Simple merge by score - in production, use more sophisticated merging
        all_results = vector_results + graph_results
        
        # Sort by score
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Deduplicate by content hash
        seen = set()
        unique_results = []
        for r in all_results:
            content_hash = hash(r.get("content", ""))
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(r)
        
        return unique_results
    
    async def _compress_context(self, results: List[Dict[str, Any]]) -> str:
        """Compress results into a single context string."""
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results):
            source = result.get("source", "unknown")
            content = result.get("content", "")[:2000]  # Limit length
            title = result.get("title", "")
            score = result.get("score", 0)
            
            context_parts.append(
                f"[{i+1}] Source: {source} | Score: {score:.3f} | Title: {title}\n{content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    async def ingest_documents(
        self,
        project_id: UUID,
        documents: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, int]:
        """Ingest documents into both stores."""
        vector_count = await self.vector_store.add_documents(project_id, documents, metadata)
        graph_count = await self.graph_store.add_documents(project_id, documents, metadata)
        
        return {
            "vector_documents": vector_count,
            "graph_documents": graph_count,
        }
    
    async def delete_project(self, project_id: UUID) -> bool:
        """Delete project from both stores."""
        await asyncio.gather(
            self.vector_store.delete_project(project_id),
            self.graph_store.delete_project(project_id),
        )
        return True


import asyncio
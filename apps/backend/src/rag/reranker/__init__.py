"""
Reranker for improving search result relevance.
"""
from typing import List, Dict, Any

from apps.backend.src.core.config import settings


class Reranker:
    """Reranks search results using cross-encoder or LLM."""
    
    def __init__(self):
        self.model_name = getattr(settings, 'RERANKER_MODEL', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
        self._model = None
    
    async def _load_model(self):
        """Load reranker model."""
        if self._model is None:
            # In production, load actual model
            # from sentence_transformers import CrossEncoder
            # self._model = CrossEncoder(self.model_name)
            pass
    
    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Rerank results by relevance to query."""
        if not results:
            return []
        
        await self._load_model()
        
        # Prepare pairs for reranking
        pairs = [(query, r.get("content", "")[:512]) for r in results]
        
        # Score pairs (placeholder - would use actual model)
        scores = await self._score_pairs(pairs)
        
        # Combine results with scores
        for i, result in enumerate(results):
            result["rerank_score"] = scores[i] if i < len(scores) else 0
            result["final_score"] = (
                result.get("score", 0) * 0.3 + result["rerank_score"] * 0.7
            )
        
        # Sort by final score
        results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return results[:top_k]
    
    async def _score_pairs(self, pairs: List[tuple]) -> List[float]:
        """Score query-document pairs."""
        # Placeholder - would use actual cross-encoder
        import random
        return [random.uniform(0.5, 1.0) for _ in pairs]


# Global instance
_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """Get or create reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
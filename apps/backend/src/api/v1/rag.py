"""
RAG pipeline endpoints.
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
from apps.backend.src.core.exceptions import NotFoundError, RAGError
from apps.backend.src.models.entities import User, Project
from apps.backend.src.rag.hybrid.pipeline import HybridRAGPipeline
from apps.backend.src.rag.vector.store import VectorStore
from apps.backend.src.rag.graph.store import GraphStore
from apps.backend.src.models.schemas import (
    RAGQuery,
    RAGResponse,
    DocumentIngest,
    DocumentIngestResponse,
)

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


@router.post("/query", response_model=RAGResponse)
async def query_rag(
    query: RAGQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Query the RAG pipeline."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    # Verify project access if specified
    if query.project_id:
        result = await db.execute(
            select(Project).where(Project.id == query.project_id, Project.owner_id == current_user.id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise NotFoundError("Project", query.project_id)
    
    try:
        pipeline = HybridRAGPipeline()
        response = await pipeline.query(
            query=query.query,
            project_id=query.project_id,
            top_k=query.top_k,
            rerank_top_k=query.rerank_top_k,
            filters=query.filters,
        )
        return response
    except Exception as e:
        raise RAGError(f"Query failed: {str(e)}")


@router.post("/ingest", response_model=DocumentIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_documents(
    ingest: DocumentIngest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Ingest documents into RAG pipeline."""
    require_permission(current_user.token_data, Permission.WORKFLOW_CREATE)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == ingest.project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", ingest.project_id)
    
    try:
        vector_store = VectorStore()
        graph_store = GraphStore()
        
        vector_count = 0
        graph_count = 0
        
        for doc in ingest.documents:
            # Index in vector store
            await vector_store.add_documents(
                project_id=ingest.project_id,
                documents=[doc],
                metadata={"source": ingest.source, "ingested_by": str(current_user.id)},
            )
            vector_count += 1
            
            # Index in graph store
            await graph_store.add_documents(
                project_id=ingest.project_id,
                documents=[doc],
                metadata={"source": ingest.source, "ingested_by": str(current_user.id)},
            )
            graph_count += 1
        
        return DocumentIngestResponse(
            project_id=ingest.project_id,
            vector_documents_indexed=vector_count,
            graph_documents_indexed=graph_count,
            message="Documents ingested successfully",
        )
    except Exception as e:
        raise RAGError(f"Ingestion failed: {str(e)}")


@router.delete("/project/{project_id}", status_code=status.HTTP_200_OK)
async def delete_project_index(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete all RAG indexes for a project."""
    require_permission(current_user.token_data, Permission.WORKFLOW_UPDATE)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        vector_store = VectorStore()
        graph_store = GraphStore()
        
        await vector_store.delete_project(project_id)
        await graph_store.delete_project(project_id)
        
        return {"message": "Project indexes deleted", "project_id": str(project_id)}
    except Exception as e:
        raise RAGError(f"Deletion failed: {str(e)}")


@router.get("/project/{project_id}/stats")
async def get_project_rag_stats(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get RAG statistics for a project."""
    require_permission(current_user.token_data, Permission.WORKFLOW_READ)
    
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", project_id)
    
    try:
        vector_store = VectorStore()
        graph_store = GraphStore()
        
        vector_stats = await vector_store.get_project_stats(project_id)
        graph_stats = await graph_store.get_project_stats(project_id)
        
        return {
            "project_id": str(project_id),
            "vector_store": vector_stats,
            "graph_store": graph_stats,
        }
    except Exception as e:
        raise RAGError(f"Stats retrieval failed: {str(e)}")
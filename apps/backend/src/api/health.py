"""
Health check endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.src.core.database import db_manager
from apps.backend.src.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": "agentforge-backend",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check - verifies all dependencies."""
    checks = {}
    overall_healthy = True
    
    # Check database
    try:
        async with db_manager.session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Check Redis
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Check Qdrant
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.QDRANT_URL}/health", timeout=5.0)
            if response.status_code == 200:
                checks["qdrant"] = {"status": "healthy"}
            else:
                checks["qdrant"] = {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
                overall_healthy = False
    except Exception as e:
        checks["qdrant"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    # Check Neo4j
    try:
        from neo4j import AsyncGraphDatabase
        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        async with driver.session() as session:
            await session.run("RETURN 1")
        await driver.close()
        checks["neo4j"] = {"status": "healthy"}
    except Exception as e:
        checks["neo4j"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "checks": checks,
    }


@router.get("/live")
async def liveness_check():
    """Liveness check - basic process health."""
    return {"status": "alive"}
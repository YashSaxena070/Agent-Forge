"""
API v1 router aggregating all endpoints.
"""
from fastapi import APIRouter

from apps.backend.src.api.v1 import (
    projects,
    workflows,
    tasks,
    agents,
    artifacts,
    deployments,
    rag,
    memory,
    approvals,
    metrics,
    websocket,
)

api_router = APIRouter()

api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(deployments.router, prefix="/deployments", tags=["deployments"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(memory.router, prefix="/memory", tags=["memory"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
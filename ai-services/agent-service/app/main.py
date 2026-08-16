from fastapi import FastAPI

from app.core.config import settings
from app.api.routes.agent import router as agent_router

app = FastAPI(
    title="AgentForge AI Agent Service",
    version=settings.service_version
)

app.include_router(agent_router)

@app.get("/health")
async def health():

    return {
        "status": "UP",
        "service": settings.service_name,
        "version": settings.service_version
    }
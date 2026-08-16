from fastapi import APIRouter

from app.agents.graph import build_agent_graph
from app.models.requests import AgentRunRequest

router = APIRouter(
    prefix="/api/v1/agents",
    tags=["Agents"]
)

agent_graph=build_agent_graph()

@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    request: AgentRunRequest
):
     
    initial_state = {
        "user_message": request.user_message,
        "system_prompt": request.system_prompt,
        "response": "",
        "error": None
    }

    result = agent_graph.invoke(
        initial_state
    )

    return {
        "success": True,
        "agentId": agent_id,
        "projectId": request.project_id,
        "response": result["response"]
    }


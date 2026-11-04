import httpx
from langgraph.graph import (
    StateGraph,
    START,
    END
)

from app.agents.state import AgentState
from app.core.config import settings


def agent_node(
    state: AgentState
) -> AgentState:

    message = state.get("user_message", "")
    system_prompt = state.get("system_prompt", "You are an expert AI software engineering agent.")

    api_key = settings.effective_api_key
    base_url = settings.model_base_url.rstrip("/")
    model = settings.model_name or "llama-3.3-70b-versatile"

    # If no API key is set yet, return an informational response
    if not api_key:
        return {
            **state,
            "response": f"Agent received: '{message}'. (Note: Please set GROQ_API_KEY in .env to enable live Groq AI responses).",
            "error": "GROQ_API_KEY not configured"
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "temperature": settings.model_temperature
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
            
            # If model name (such as gpt-110b) isn't hosted directly on Groq's endpoint, fall back to llama-3.3-70b-versatile
            if resp.status_code == 404 and model.lower() != "llama-3.3-70b-versatile":
                fallback_payload = {**payload, "model": "llama-3.3-70b-versatile"}
                resp = client.post(f"{base_url}/chat/completions", headers=headers, json=fallback_payload)

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    **state,
                    "response": content,
                    "error": None
                }
            else:
                error_msg = f"Groq API Error ({resp.status_code}): {resp.text}"
                return {
                    **state,
                    "response": f"Agent received: {message} (API returned {resp.status_code})",
                    "error": error_msg
                }
    except Exception as e:
        return {
            **state,
            "response": f"Agent execution fallback: {message}",
            "error": str(e)
        }


def build_agent_graph():

    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)

    return graph.compile()

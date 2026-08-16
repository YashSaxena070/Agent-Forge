from langgraph.graph import (
    StateGraph,
    START,
    END
)

from app.agents.state import AgentState

def agent_node(
    state: AgentState
) -> AgentState:

    message=state["user_message"]

    system_prompt=state["system_prompt"]

    response=(
        f"Agent received: {message}"
    )

    return {
        **state,
        "response":response,
        "error":None
    }

def build_agent_graph():

    graph = StateGraph(AgentState)

    graph.add_node("agent",agent_node)
    graph.add_edge(START,"agent")
    graph.add_edge("agent",END)

    return graph.compile()
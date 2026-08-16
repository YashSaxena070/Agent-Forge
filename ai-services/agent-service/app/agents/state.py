from typing import TypedDict, Optional


class AgentState(TypedDict):
    user_message: str
    system_prompt: Optional[str]
    response: Optional[str]
    error: Optional[str]

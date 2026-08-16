from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):

    agent_id: str

    project_id: str

    user_message: str = Field(
        min_length=1,
        max_length=10000
    )

    system_prompt: str = Field(
        min_length=1,
        max_length=20000
    )
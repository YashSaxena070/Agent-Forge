from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    service_name: str = "agentforge-agent-service"

    service_version: str = "0.1.0"

    spring_boot_url: str = "http://localhost:8080"

    model_provider: str = "OPENAI_COMPATIBLE"
    model_base_url: str = "https://api.groq.com/openai/v1"
    model_api_key: str = ""
    groq_api_key: Optional[str] = None

    model_name: str = "llama-3.3-70b-versatile"

    model_temperature: float = 0.7

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def effective_api_key(self) -> str:
        return self.model_api_key or self.groq_api_key or ""


settings = Settings()

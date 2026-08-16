from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    service_name: str = "agentforge-agent-service"

    service_version: str = "0.1.0"

    spring_boot_url: str = "http://localhost:8080"

    model_provider: str = "OPENAI_COMPATIBLE"
    model_base_url: str = "http://localhost:20128/v1"
    model_api_key: str = ""

    model_name: str = "auto"

    model_temperature: float = 0.7

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
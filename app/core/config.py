from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["demo", "full"] = "demo"
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8102, ge=1, le=65535)
    database_url: str = "sqlite:///./data/agent_demo.db"
    llm_provider: Literal["mock", "deepseek"] = "mock"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    redis_url: str = ""
    data_dir: Path = Path("data")

    @model_validator(mode="after")
    def validate_mode(self) -> "Settings":
        if self.app_env == "demo" and self.llm_provider != "mock":
            raise ValueError("Demo mode requires LLM_PROVIDER=mock")
        if self.llm_provider == "deepseek" and not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

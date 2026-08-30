from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    LLM_MODEL: str
    LLM_BASE_URL: str
    LLM_CONCURENT_REQ: int
    LLM_API_KEY: str

    PRODUCTION: bool

    DSN: str
  
settings = Settings()	  
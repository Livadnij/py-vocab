from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
  
    GOOGLE_SERVICE_ACCOUNT_JSON_STOCK: dict[str, Any]
    STOCK_SHEET_RANGE: str
    STOCK_SHEET_ID: str

    GOOGLE_SERVICE_ACCOUNT_JSON_PRODUCTS: dict[str, Any]
    PRODUCTS_SHEET_ID: str
    PRODUCTS_SHEET_RANGE: str

    LLM_MODEL: str
    LLM_BASE_URL: str
    LLM_CONCURENT_REQ: int
    LLM_API_KEY: str

    CATEGORY: str

    PRODUCTION: bool

    DSN: str
  
settings = Settings()	  
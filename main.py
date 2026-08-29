from src.config import settings
from src.db.database import Database
from src.llm.llm import LLLM

from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.api import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database(settings.DSN)
    llm = LLLM(settings.LLM_BASE_URL, settings.LLM_API_KEY)
    yield {"db": db, "llm": llm}
    db.close()

app = FastAPI(
    lifespan=lifespan,
    docs_url=None if settings.PRODUCTION else "/docs",
    redoc_url=None if settings.PRODUCTION else "/redoc",
    openapi_url=None if settings.PRODUCTION else "/openapi.json",
    )

app.include_router(router, prefix="/api/v1")

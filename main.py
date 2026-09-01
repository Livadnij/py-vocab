import asyncio
import logging
import uvicorn

from src.config import settings
from src.db.database import Database
from src.llm.llm import LLLM

from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.api import router
from src.worker.state import WorkerState
from src.db.crud import attempt as crud_attempt

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_state = WorkerState()
    db = Database(settings.DSN)
    llm = LLLM(settings.LLM_BASE_URL, settings.LLM_API_KEY)

    async with db.session() as session:
        await crud_attempt.recover_stuck_attempts(session)

    yield {"db": db, "llm": llm, "worker_state": worker_state}

    if worker_state.task is not None:
        worker_state.task.cancel()
        try:
            await worker_state.task
        except asyncio.CancelledError:
            pass

    await db.close()

app = FastAPI(
    lifespan=lifespan,
    docs_url=None if settings.PRODUCTION else "/docs",
    redoc_url=None if settings.PRODUCTION else "/redoc",
    openapi_url=None if settings.PRODUCTION else "/openapi.json",
    )

app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    logging.basicConfig(
        level= logging.INFO if settings.PRODUCTION else logging.DEBUG,
    )
    uvicorn.run(app)
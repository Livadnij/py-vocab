import asyncio

from src.config import settings
from src.db.models import  ProcessingAttempt

from src.db.database import Database
from src.llm.llm import LLLM
from src.db.crud import hard_error as crud_hard_error,  request as crud_request, hard_error as crud_hard_error
from datetime import timedelta
from time import monotonic

from src.service.title import process_title
from src.worker.state import WorkerState


async def run_process(db: Database, llm: LLLM, request_attempts: list[ProcessingAttempt], request_id: int, worker_state: WorkerState) -> None:
    start = monotonic()
    halt_event = asyncio.Event()
    systemic_error: list[str] = []

    try:
        titles_len = len(request_attempts)

        semaphore = asyncio.Semaphore(settings.LLM_CONCURENT_REQ)
        await asyncio.gather(*(
            process_title(semaphore, llm, db, attempt, settings.LLM_MODEL, i, titles_len, halt_event, systemic_error)
            for i, attempt in enumerate(request_attempts)
        ))
        if halt_event.is_set() and systemic_error:
            async with db.session() as session:
                await crud_hard_error.create_hard_error(session, systemic_error[0], request_id)
                await session.commit()
            worker_state.enabled.clear()
    finally:
        duration = timedelta(seconds=monotonic() - start)
        async with db.session() as session:
            await crud_request.update_request(session, request_id, elapsed_time=duration)
            await session.commit()
        print(f'Done category')


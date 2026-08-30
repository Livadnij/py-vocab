import asyncio
from src.db.database import Database
from src.llm.llm import LLLM
from src.worker.state import WorkerState
from src.db.crud import attempt as crud_attempt, request as crud_request
from src.service import processing as service_attempt
import logging


logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 5


async def worker_loop(db: Database, llm: LLLM, state: WorkerState):
    while True:
        await state.enabled.wait()

        try:
            state.is_processing = True
            found_work = await process_batch(db, llm, state)
        except Exception:
            logger.exception("worker loop iteration failed")
            found_work = False
        finally:
            state.is_processing = False

        if not found_work:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def process_batch(db: Database, llm: LLLM, state: WorkerState) -> bool:
    async with db.session() as session:
        request_inst = await crud_request.get_next_request_with_pending_attempts(session)
       
        if not request_inst:
            return False
        request_attempts = await crud_attempt.get_pending_attempts_for_request(session=session, request_id=request_inst.id)

    await service_attempt.run_process(db, llm, request_attempts, request_id=request_inst.id, worker_state=state)

    return True
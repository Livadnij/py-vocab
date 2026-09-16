from src.db.database import Database
from src.db.models import Prompt
from src.llm.llm import LLLM
from src.worker.state import WorkerState
from src.db.crud import attempt as crud_attempt
from src.service import processing as service_processing
import logging

from src.db.crud import (
    prompt as crud_prompt,
    hard_error as crud_hard_error
    )


logger = logging.getLogger(__name__)


async def resolve_default_prompt(session) -> tuple[Prompt | None, str | None]:
    prompt = await crud_prompt.get_default_prompt(session)
    error = "no default prompt configured" if prompt is None else None
    return prompt, error


async def process_pending(db: Database, llm: LLLM, state: WorkerState, limit: int | None = None) -> None:
    try:
        state.is_processing = True
        async with db.session() as session:
            attempts = await crud_attempt.get_pending_attempts(session, limit=limit)
            if not attempts:
                return

            prompt, error = await resolve_default_prompt(session)
            if error:
                await crud_hard_error.create_hard_error(session, error)
                await session.commit()
                return

        await service_processing.run_process(db, llm, attempts, prompt.id, prompt.prompt)
    finally:
        state.is_processing = False
        state.task = None
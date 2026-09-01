from src.db.database import Database
from src.db.models import Prompt
from src.llm.llm import LLLM
from src.worker.state import WorkerState
from src.db.crud import attempt as crud_attempt, request as crud_request
from src.service import processing as service_attempt
import logging

from src.db.crud import (
    prompt as crud_prompt,
    hard_error as crud_hard_error
    )


logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 5

async def resolve_prompt(session, request_inst) -> tuple[Prompt | None, str | None]:
    if request_inst.selected_prompt_id is not None:
        prompt = await crud_prompt.get_prompt_by_id(session, request_inst.selected_prompt_id)
        error = f"selected_prompt_id {request_inst.selected_prompt_id} not found" if prompt is None else None
    else:
        prompt = await crud_prompt.get_default_prompt(session)
        error = "no default prompt configured" if prompt is None else None
    return prompt, error


async def process_requests(db: Database, llm: LLLM, request_ids: list[int], state: WorkerState) -> None:
    try:
        state.is_processing = True
        for request_id in request_ids:
            async with db.session() as session:
                row = await crud_request.get_request_by_id(session, request_id)
                if row is None:
                    continue
                request_attempts = await crud_attempt.get_pending_attempts_for_request(session=session, request_id=request_id)
                if not request_attempts:
                    continue

                prompt, error = await resolve_prompt(session, row.Request)
                if error:
                    await crud_hard_error.create_hard_error(session, error, request_id)
                    await session.commit()
                    continue

            halted = await service_attempt.run_process(db, llm, request_attempts, request_id, prompt.id, prompt.prompt)
            if halted:
                break
    finally:
        state.is_processing = False
        state.task = None
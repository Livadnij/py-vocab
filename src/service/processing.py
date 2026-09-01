import asyncio

from src.config import settings
from src.db.models import  AttemptStatus, ProcessingAttempt

from src.db.database import Database
from src.llm.llm import LLLM, ExtractionResult
from src.db.crud import (
    thinking as crud_thinking,
    attempt as crud_attempt,
    attempt_error as crud_attempt_error,
    token as crud_token,
    hard_error as crud_hard_error,
    request as crud_request,
    title as crud_title
)
from datetime import timedelta
from time import monotonic

from src.llm.parsing import ResponseParsingError, parse_extraction_response
from src.service.llm import LLMCallError, LLMSystemicError, extract_raw_tokens, normalize_tokens
from src.worker.state import WorkerState


async def run_process(db: Database, llm: LLLM, request_attempts: list[ProcessingAttempt], request_id: int, prompt_id: int, prompt_text: str) -> bool:
    """Returns True if a systemic failure halted this request."""
    start = monotonic()
    halt_event = asyncio.Event()
    systemic_error: list[str] = []

    try:
        titles_len = len(request_attempts)
        semaphore = asyncio.Semaphore(settings.LLM_CONCURENT_REQ)
        await asyncio.gather(*(
            process_title(semaphore, llm, db, attempt, settings.LLM_MODEL, prompt_id, prompt_text, i, titles_len, halt_event, systemic_error)
            for i, attempt in enumerate(request_attempts)
        ))
        if halt_event.is_set() and systemic_error:
            async with db.session() as session:
                await crud_hard_error.create_hard_error(session, systemic_error[0], request_id)
                await session.commit()
            return True
        return False
    finally:
        duration = timedelta(seconds=monotonic() - start)
        async with db.session() as session:
            await crud_request.update_request(session, request_id, elapsed_time=duration)
            await session.commit()
            

async def run_llm_extraction(
    semaphore: asyncio.Semaphore,
    llm: LLLM,
    db: Database,
    attempt: ProcessingAttempt,
    model: str,
    prompt_text: str,
    title_log: list[str],
    halt_event: asyncio.Event,
    systemic_error: list[str],
) -> ExtractionResult | None:
    """Marks the attempt running and calls the LLM. Returns None if the attempt
    should stop here — either a per-title failure or a halted batch."""
    async with semaphore:
        if halt_event.is_set():
            return None

        async with db.session() as session:
            await crud_attempt.update_attempt_status(session, attempt.id, AttemptStatus.running)
            await session.commit()

        title_log.append(f'Starting processing {attempt.title.title}')

        try:
            return await extract_raw_tokens(attempt, model, llm, prompt_text, title_log)
        except LLMSystemicError as e:
            async with db.session() as session:
                await crud_attempt.update_attempt_status(session, attempt.id, AttemptStatus.failed)
                await session.commit()

            if not halt_event.is_set():
                halt_event.set()
                systemic_error.append(str(e))

            print("\n".join(title_log))
            return None
        except LLMCallError as e:
            async with db.session() as session:
                await crud_attempt_error.create_attempt_error(session, str(e), attempt.id)
                await crud_attempt.update_attempt_status(session, attempt.id, AttemptStatus.failed)
                await session.commit()
            print("\n".join(title_log))
            return None


async def process_extraction_result(
    db: Database, attempt: ProcessingAttempt, llm_response: ExtractionResult, prompt_id: int, title_log: list[str]
) -> None:
    """Parses, normalizes, and persists a successful LLM response, finalizing the attempt's status."""
    async with db.session() as session:
        try:
            await crud_thinking.create_thinking(session, llm_response, attempt.id, prompt_id)
            await session.commit()
        except Exception as e:
            await session.rollback()
            title_log.append(f"Unexpected error creating Thinking record: {e}")
            async with db.session() as retry_session:
                await crud_attempt_error.create_attempt_error(retry_session, str(e), attempt.id)
                await crud_attempt.update_attempt_status(retry_session, attempt.id, AttemptStatus.failed)
                await retry_session.commit()
            print("\n".join(title_log))
            return

    try:
        token_list = parse_extraction_response(llm_response)
    except ResponseParsingError as e:
        async with db.session() as session:
            await crud_attempt_error.create_attempt_error(session, str(e), attempt.id)
            await crud_attempt.update_attempt_status(session, attempt.id, AttemptStatus.failed)
            await session.commit()
        return

    async with db.session() as session:
        validated_token_list = await normalize_tokens(session, attempt, token_list, title_log)
        if not validated_token_list:
            message = "No tokens remained after normalization"
            await crud_attempt_error.create_attempt_error(session, message, attempt.id)
            await crud_attempt.update_attempt_status(session, attempt.id, AttemptStatus.failed)
            await session.commit()
            return

        title = await crud_title.get_title_with_vocab(session, attempt.title_id)

        try:
            await crud_token.persist_tokens(session, validated_token_list, title_log, title)
        except Exception as e:
            title_log.append(f"Unexpected error persisting tokens: {e}")
            await session.rollback()
            async with db.session() as retry_session:
                await crud_attempt_error.create_attempt_error(retry_session, str(e), attempt.id)
                await crud_attempt.update_attempt_status(retry_session, attempt.id, AttemptStatus.failed)
                await retry_session.commit()
            print("\n".join(title_log))
            return

        await crud_attempt.update_attempt_status(session, attempt.id, AttemptStatus.succeeded)
        await session.commit()


async def process_title(semaphore, llm, db, attempt, model, prompt_id: int, prompt_text: str, i, category_len, halt_event, systemic_error) -> None:
    title_log = [f'[{i+1}/{category_len}]']
    llm_response = await run_llm_extraction(semaphore, llm, db, attempt, model, prompt_text, title_log, halt_event, systemic_error)
    if llm_response is None:
        return
    await process_extraction_result(db, attempt, llm_response, prompt_id, title_log)

    title_log.append('Done\n')
    print("\n".join(title_log))
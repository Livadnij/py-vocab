from pydantic import ValidationError

from sqlalchemy.ext.asyncio import AsyncSession
from src.llm.llm import LLLM, ExtractionResult
from src.db.models import ProcessingAttempt
from src.schemas import TitlesList, TokenBase, TokenList

from src.db.crud import attempt_error as crud_attempt_error

from openai import APIError, APIConnectionError, APITimeoutError, AuthenticationError

from datetime import timedelta
from time import monotonic


async def normalize_tokens(session, attempt, token_list: TokenList, title_log: list[str]) -> list[TokenBase]:
    start = monotonic()
    title = attempt.title.title

    tokens = []
    for t in token_list.tokens:
        if t.token.lower() in title.lower():
            tokens.append(t)
        else:
            message = f"'{t.token}' doesn't exist in title: '{title}'. Dropping token"
            await crud_attempt_error.create_attempt_error(session, message, attempt.id)
            title_log.append(message)

    duration = timedelta(seconds=monotonic() - start)
    title_log.append(f'Tokens processed: {tokens}, in {duration.total_seconds()} sec.')
    return tokens


class LLMCallError(Exception):
    """A single title's LLM call failed — not systemic."""


class LLMSystemicError(LLMCallError):
    """The LLM service itself is unusable — affects every remaining title."""


async def extract_raw_tokens(attempt: ProcessingAttempt, model: str, llm: LLLM, title_log: list[str]) -> ExtractionResult:
    try:
        response = await llm.extract(attempt.title.title, model)
        title_log.append(f'LLM response received in {response.duration.total_seconds()} sec.')
        return response
    except AuthenticationError as e:
        title_log.append(f"LLM auth failure: {e}")
        print("\n".join(title_log))
        raise LLMSystemicError(str(e)) from e
    except (APIConnectionError, APITimeoutError, APIError) as e:
        title_log.append(f"LLM call failed for title: {e}")
        print("\n".join(title_log))
        raise LLMCallError(str(e)) from e
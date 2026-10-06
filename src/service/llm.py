from src.llm.llm import LLLM, ExtractionResult
from src.db.models import ProcessingAttempt
from src.schemas.token import TokenBase, TokenList

from src.db.crud import attempt_error as crud_attempt_error
from src.utils.normalize import normalize_title_words, normalize_word

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
)

from datetime import timedelta
from time import monotonic


async def validate_tokens(session, attempt, token_list: TokenList, title_log: list[str]) -> list[TokenBase]:
    start = monotonic()
    title = attempt.title.title
    title_words = normalize_title_words(title)

    tokens = []
    for t in token_list.tokens:
        word = normalize_word(t.token)
        if word in title_words:
            tokens.append(TokenBase(token=word, label=t.label))
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


async def extract_raw_tokens(attempt: ProcessingAttempt, model: str, llm: LLLM, prompt: str, title_log: list[str]) -> ExtractionResult:
    try:
        response = await llm.extract(attempt.title.title, model, prompt)
        title_log.append(f'LLM response received in {response.duration.total_seconds()} sec.')
        return response
    except APITimeoutError as e:
        title_log.append(f"LLM call timed out for title: {e}")
        print("\n".join(title_log))
        raise LLMCallError(str(e)) from e
    except (AuthenticationError, PermissionDeniedError, NotFoundError, APIConnectionError) as e:
        title_log.append(f"LLM service unusable: {e}")
        print("\n".join(title_log))
        raise LLMSystemicError(str(e)) from e
    except APIError as e:
        title_log.append(f"LLM call failed for title: {e}")
        print("\n".join(title_log))
        raise LLMCallError(str(e)) from e
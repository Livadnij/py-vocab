from src.db.database import Database
from src.db.crud import attempt as crud_attempt, attempt_error as crud_attempt_error
from src.schemas.thinking import ThinkingOut
from src.schemas.title import AttemptDetailOut, AttemptErrorOut


async def get_attempt_detail(db: Database, attempt_id: int) -> AttemptDetailOut | None:
    async with db.session() as session:
        row = await crud_attempt.get_attempt_detail(session, attempt_id)
        if row is None:
            return None

        thinking = None
        if row.model is not None:
            thinking = ThinkingOut(
                used_prompt_id=row.used_prompt_id,
                model=row.model,
                finish_reason=row.finish_reason,
                prompt_tokens=row.prompt_tokens,
                completion_tokens=row.completion_tokens,
                reasoning_tokens=row.reasoning_tokens,
                duration=row.duration,
                text=row.text,
                response=row.response,
            )

        error_rows = await crud_attempt_error.get_errors_for_attempt(session, attempt_id)
        errors = [
            AttemptErrorOut(id=e.id, message=e.message, created_at=e.created_at)
            for e in error_rows
        ]

        return AttemptDetailOut(
            id=row.ProcessingAttempt.id,
            status=row.ProcessingAttempt.status,
            created_at=row.ProcessingAttempt.created_at,
            attempt_error_count=row.attempt_error_count,
            thinking=thinking,
            prompt=row.prompt,
            errors=errors,
        )
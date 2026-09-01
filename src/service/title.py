from src.db.database import Database
from src.db.crud import (
    title as crud_title,
)
from src.schemas.thinking import ThinkingOut
from src.schemas.title import TitleDetailOut


async def get_title_by_request(db: Database, request_id: int, title_id: int) -> TitleDetailOut | None:
    async with db.session() as session:
        row = await crud_title.get_title_by_id_and_request(session, request_id, title_id)
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

        return TitleDetailOut(
            id=row.Title.id,
            title=row.Title.title,
            created_at=row.Title.created_at,
            status=row.status,
            brands=[b.name for b in row.Title.brands],
            tier_words=[t.name for t in row.Title.tier_words],
            descriptors=[d.name for d in row.Title.descriptors],
            attempt_error_count=row.attempt_error_count,
            thinking=thinking,
        )

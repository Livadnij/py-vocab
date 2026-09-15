from src.db.database import Database
from src.db.crud import (
    title as crud_title,
    token as crud_token,
    attempt as crud_attempt,
)
from src.schemas.common import PaginationOut
from src.schemas.thinking import ThinkingOut
from src.schemas.title import AttemptOut, TitleBase, TitleDetailOut, TitleListQuery, TitleWithAttemptsOut, TitleWithRequestsListOut, TitleWithRequestsOut, WordWithOccurrence


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

        brand_occurrences = await crud_token.get_brand_occurrences(session, [b.id for b in row.Title.brands])
        tier_word_occurrences = await crud_token.get_tier_word_occurrences(session, [t.id for t in row.Title.tier_words])
        descriptor_occurrences = await crud_token.get_descriptor_occurrences(session, [d.id for d in row.Title.descriptors])

        brands = [
            WordWithOccurrence(id=b.id, name=b.name, occurrence=brand_occurrences[b.id])
            for b in row.Title.brands
        ]
        tier_words = [
            WordWithOccurrence(id=t.id, name=t.name, occurrence=tier_word_occurrences[t.id])
            for t in row.Title.tier_words
        ]
        descriptors = [
            WordWithOccurrence(id=d.id, name=d.name, occurrence=descriptor_occurrences[d.id])
            for d in row.Title.descriptors
        ]

        return TitleDetailOut(
            id=row.Title.id,
            title=row.Title.title,
            created_at=row.Title.created_at,
            status=row.status,
            brands=brands,
            tier_words=tier_words,
            descriptors=descriptors,
            attempt_error_count=row.attempt_error_count,
            thinking=thinking,
        )

async def create_titles(db: Database, titles: list[str]) -> list[TitleBase]:
    async with db.session() as session:
        title_insts = await crud_title.get_or_create_titles(session, titles)
        await session.commit()
        return [
            TitleBase(id=t.id, title=t.title, created_at=t.created_at)
            for t in title_insts
        ]

async def list_titles(db: Database, query: TitleListQuery) -> TitleWithRequestsListOut:
    async with db.session() as session:
        rows = await crud_title.list_titles(session, query)
        total = await crud_title.count_titles(session, query)

    items = [
        TitleWithRequestsOut(
            id=row.Title.id,
            title=row.Title.title,
            created_at=row.Title.created_at,
            brand_count=row.brand_count,
            tier_word_count=row.tier_word_count,
            descriptor_count=row.descriptor_count,
        )
        for row in rows
    ]
    return TitleWithRequestsListOut(
        items=items,
        pagination=PaginationOut(limit=query.limit, offset=query.offset, total=total),
    )

async def get_title_detail(db: Database, title_id: int) -> TitleWithAttemptsOut | None:
    async with db.session() as session:
        title = await crud_title.get_title_with_vocab(session, title_id)
        if title is None:
            return None

        attempt_rows = await crud_attempt.get_attempts_for_title(session, title_id)

        brand_occurrences = await crud_token.get_brand_occurrences(session, [b.id for b in title.brands])
        tier_word_occurrences = await crud_token.get_tier_word_occurrences(session, [t.id for t in title.tier_words])
        descriptor_occurrences = await crud_token.get_descriptor_occurrences(session, [d.id for d in title.descriptors])

        brands = [
            WordWithOccurrence(id=b.id, name=b.name, occurrence=brand_occurrences[b.id])
            for b in title.brands
        ]
        tier_words = [
            WordWithOccurrence(id=t.id, name=t.name, occurrence=tier_word_occurrences[t.id])
            for t in title.tier_words
        ]
        descriptors = [
            WordWithOccurrence(id=d.id, name=d.name, occurrence=descriptor_occurrences[d.id])
            for d in title.descriptors
        ]

        attempts = [
            AttemptOut(
                id=row.ProcessingAttempt.id,
                request_id=row.ProcessingAttempt.request_id,
                status=row.ProcessingAttempt.status,
                created_at=row.ProcessingAttempt.created_at,
                attempt_error_count=row.attempt_error_count,
            )
            for row in attempt_rows
        ]

        return TitleWithAttemptsOut(
            id=title.id,
            title=title.title,
            created_at=title.created_at,
            brands=brands,
            tier_words=tier_words,
            descriptors=descriptors,
            attempts=attempts,
        )
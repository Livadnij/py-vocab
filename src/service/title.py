from src.db.database import Database
from src.db.crud import (
    title as crud_title,
    token as crud_token,
)
from src.db.models import ProcessingAttempt
from src.schemas.common import PaginationOut
from src.schemas.thinking import ThinkingOut
from src.schemas.title import RequestSummary, TitleBase, TitleDetailOut, TitleListQuery, TitleWithRequestsListOut, TitleWithRequestsOut, WordWithOccurrence


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
        total = await crud_title.count_titles(session)

        title_ids = [row.Title.id for row in rows]
        attempts = await crud_title.get_attempts_for_titles(session, title_ids)

    attempts_by_title: dict[int, list[ProcessingAttempt]] = {}
    for a in attempts:
        attempts_by_title.setdefault(a.title_id, []).append(a)

    items = [
        TitleWithRequestsOut(
            id=row.Title.id,
            title=row.Title.title,
            created_at=row.Title.created_at,
            brand_count=row.brand_count,
            tier_word_count=row.tier_word_count,
            descriptor_count=row.descriptor_count,
            requests=[
                RequestSummary(request_id=a.request_id, status=a.status)
                for a in attempts_by_title.get(row.Title.id, [])
            ],
        )
        for row in rows
    ]
    return TitleWithRequestsListOut(
        items=items,
        pagination=PaginationOut(limit=query.limit, offset=query.offset, total=total),
    )
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload
from src.db.models import ProcessingAttempt, Title

async def create_title(session: AsyncSession, title: str, request_id: int) -> Title:
    title_inst = Title(title=title, request_id=request_id)
    session.add(title_inst)
    await session.flush()
    return title_inst

async def get_titles_by_title(session: AsyncSession, titles: list[str]) -> set[str]:
    return set( await session.scalars(
        select(Title.title)
        .where(Title.title.in_(titles))
        ))

async def get_titles_by_ids(session: AsyncSession, title_ids: list[int]) -> list[Title]:
    return list( await session.scalars(
        select(Title)
        .where(Title.id.in_(title_ids))
        ))

async def get_titles_by_request_id(session: AsyncSession, request_id: int) -> list[Title]:
    stmt = (
        select(Title)
        .join(Title.attempts)
        .where(ProcessingAttempt.request_id == request_id)
        .options(contains_eager(Title.attempts))
    )
    result = await session.scalars(stmt)
    return list(result.unique().all())
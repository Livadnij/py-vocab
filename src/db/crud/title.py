from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.models import ProcessingAttempt, Title, TitleBrand, TitleDescriptor, TitleTierWord
from src.schemas.title import TitleListQuery


async def get_title_with_vocab(session: AsyncSession, title_id: int) -> Title | None:
    return await session.get(
        Title,
        title_id,
        options=[
            selectinload(Title.brands),
            selectinload(Title.tier_words),
            selectinload(Title.descriptors),
        ],
    )

async def create_title(session: AsyncSession, title: str) -> Title:
    title_inst = Title(title=title)
    session.add(title_inst)
    await session.flush()
    return title_inst

async def get_titles_by_ids(session: AsyncSession, title_ids: list[int]) -> list[Title]:
    return list(await session.scalars(
        select(Title)
        .where(Title.id.in_(title_ids))
        ))

def _brand_count():
    return (
        select(func.count(TitleBrand.brand_id))
        .where(TitleBrand.title_id == Title.id)
        .correlate(Title)
        .scalar_subquery()
    )

def _tier_word_count():
    return (
        select(func.count(TitleTierWord.tier_word_id))
        .where(TitleTierWord.title_id == Title.id)
        .correlate(Title)
        .scalar_subquery()
    )

def _descriptor_count():
    return (
        select(func.count(TitleDescriptor.descriptor_id))
        .where(TitleDescriptor.title_id == Title.id)
        .correlate(Title)
        .scalar_subquery()
    )

def _attempt_count():
    return (
        select(func.count(ProcessingAttempt.id))
        .where(ProcessingAttempt.title_id == Title.id)
        .correlate(Title)
        .scalar_subquery()
    )


async def get_or_create_titles(session: AsyncSession, titles: list[str]) -> tuple[list[Title], list[Title]]:
    """Returns (existing, newly_created)."""
    unique_titles = list(dict.fromkeys(titles))
    result = await session.scalars(select(Title).where(Title.title.in_(unique_titles)))
    existing_map = {t.title: t for t in result}

    existing = []
    newly_created = []
    for t in unique_titles:
        if t in existing_map:
            existing.append(existing_map[t])
        else:
            title_inst = Title(title=t)
            session.add(title_inst)
            newly_created.append(title_inst)

    await session.flush()
    return existing, newly_created

async def list_titles(session: AsyncSession, query: TitleListQuery):
    attempt_count = _attempt_count()
    brand_count = _brand_count()
    tier_word_count = _tier_word_count()
    descriptor_count = _descriptor_count()

    SORT_COLUMNS = {
        "id": Title.id,
        "title": Title.title,
        "created_at": Title.created_at,
        "attempt_count": attempt_count,
        "brand_count": brand_count,
        "tier_word_count": tier_word_count,
        "descriptor_count": descriptor_count,
        "total_word_count": brand_count + tier_word_count + descriptor_count,
    }
    sort_column = SORT_COLUMNS.get(query.sort, attempt_count)
    order_clause = sort_column.asc() if query.order == "asc" else sort_column.desc()

    stmt = select(
        Title,
        attempt_count.label("attempt_count"),
        brand_count.label("brand_count"),
        tier_word_count.label("tier_word_count"),
        descriptor_count.label("descriptor_count"),
    )
    if query.q:
        stmt = stmt.where(Title.title.ilike(f"%{query.q}%"))
    stmt = stmt.order_by(order_clause).limit(query.limit).offset(query.offset)

    result = await session.execute(stmt)
    return result.all()

async def count_titles(session: AsyncSession, query: TitleListQuery) -> int:
    stmt = select(func.count()).select_from(Title)
    if query.q:
        stmt = stmt.where(Title.title.ilike(f"%{query.q}%"))
    return await session.scalar(stmt) or 0
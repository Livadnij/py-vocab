from sqlalchemy import and_, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload
from src.db.models import AttemptError, AttemptStatus, ProcessingAttempt, Thinking, Title, TitleBrand, TitleDescriptor, TitleTierWord
from src.schemas.title import RequestGetQuery, TitleListQuery


def _title_attempt_id(request_id: int):
    return (
        select(ProcessingAttempt.id)
        .where(
            ProcessingAttempt.title_id == Title.id,
            ProcessingAttempt.request_id == request_id,
        )
        .correlate(Title)
        .limit(1)
        .scalar_subquery()
    )



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

def _title_in_request(request_id: int):
    return exists().where(
        ProcessingAttempt.title_id == Title.id,
        ProcessingAttempt.request_id == request_id,
    )

def _title_used_prompt_id(request_id: int):
    return (
        select(Thinking.used_prompt_id)
        .join(ProcessingAttempt, Thinking.attempt_id == ProcessingAttempt.id)
        .where(
            ProcessingAttempt.title_id == Title.id,
            ProcessingAttempt.request_id == request_id,
        )
        .correlate(Title)
        .limit(1)
        .scalar_subquery()
    )

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

def _attempt_error_count(request_id: int):
    return (
        select(func.count(AttemptError.id))
        .join(ProcessingAttempt, AttemptError.attempt_id == ProcessingAttempt.id)
        .where(
            ProcessingAttempt.title_id == Title.id,
            ProcessingAttempt.request_id == request_id,
        )
        .correlate(Title)
        .scalar_subquery()
    )

def _title_has_attempt_status(request_id: int, status: AttemptStatus):
    return exists().where(
        ProcessingAttempt.title_id == Title.id,
        ProcessingAttempt.request_id == request_id,
        ProcessingAttempt.status == status,
    )

def _title_status(request_id: int):
    return (
        select(ProcessingAttempt.status)
        .where(
            ProcessingAttempt.title_id == Title.id,
            ProcessingAttempt.request_id == request_id,
        )
        .correlate(Title)
        .limit(1)
        .scalar_subquery()
    )

def _title_total_tokens(request_id: int):
    return (
        select(
            func.coalesce(
                func.sum(Thinking.completion_tokens + func.coalesce(Thinking.reasoning_tokens, 0)),
                0,
            )
        )
        .join(ProcessingAttempt, Thinking.attempt_id == ProcessingAttempt.id)
        .where(
            ProcessingAttempt.title_id == Title.id,
            ProcessingAttempt.request_id == request_id,
        )
        .correlate(Title)
        .scalar_subquery()
    )

def _request_count():
    return (
        select(func.count(ProcessingAttempt.id))
        .where(ProcessingAttempt.title_id == Title.id)
        .correlate(Title)
        .scalar_subquery()
    )


async def list_titles_for_request(session: AsyncSession, request_id: int, query: RequestGetQuery):
    brand_count = _brand_count()
    tier_word_count = _tier_word_count()
    descriptor_count = _descriptor_count()
    attempt_error_count = _attempt_error_count(request_id)
    status = _title_status(request_id)
    total_tokens = _title_total_tokens(request_id)
    used_prompt_id = _title_used_prompt_id(request_id)
    attempt_id = _title_attempt_id(request_id)

    SORT_COLUMNS = {
        "title": Title.title,
        "brand_count": brand_count,
        "tier_word_count": tier_word_count,
        "descriptor_count": descriptor_count,
        "total_word_count": brand_count + tier_word_count + descriptor_count,
        "attempt_error_count": attempt_error_count,
        "status": status,
        "total_tokens": total_tokens,
    }
    sort_column = SORT_COLUMNS.get(query.sort, Title.title)
    order_clause = sort_column.asc() if query.order == "asc" else sort_column.desc()

    stmt = select(
        Title,
        brand_count.label("brand_count"),
        tier_word_count.label("tier_word_count"),
        descriptor_count.label("descriptor_count"),
        attempt_error_count.label("attempt_error_count"),
        status.label("status"),
        total_tokens.label("total_tokens"),
        used_prompt_id.label("used_prompt_id"),
        attempt_id.label("attempt_id"),
    ).where(_title_in_request(request_id))
    if query.status is not None:
        stmt = stmt.where(_title_has_attempt_status(request_id, query.status))

    stmt = stmt.order_by(order_clause).limit(query.limit).offset(query.offset)

    result = await session.execute(stmt)
    return result.all()

async def count_titles_for_request(session: AsyncSession, request_id: int, query: RequestGetQuery) -> int:
    stmt = select(func.count()).select_from(Title).where(_title_in_request(request_id))
    if query.status is not None:
        stmt = stmt.where(_title_has_attempt_status(request_id, query.status))
    return await session.scalar(stmt) or 0

async def get_title_by_id_and_request(session: AsyncSession, request_id: int, title_id: int):
    attempt_error_count = _attempt_error_count(request_id)

    stmt = (
        select(
            Title,
            ProcessingAttempt.status,
            attempt_error_count.label("attempt_error_count"),
            Thinking.used_prompt_id,
            Thinking.model,
            Thinking.finish_reason,
            Thinking.prompt_tokens,
            Thinking.completion_tokens,
            Thinking.reasoning_tokens,
            Thinking.duration,
            Thinking.text,
            Thinking.response,
        )
        .join(ProcessingAttempt, and_(
            ProcessingAttempt.title_id == Title.id,
            ProcessingAttempt.request_id == request_id,
        ))
        .outerjoin(Thinking, Thinking.attempt_id == ProcessingAttempt.id)
        .where(Title.id == title_id)
        .options(
            selectinload(Title.brands),
            selectinload(Title.tier_words),
            selectinload(Title.descriptors),
        )
    )
    result = await session.execute(stmt)
    return result.first()

async def get_or_create_titles(session: AsyncSession, titles: list[str]) -> list[Title]:
    unique_titles = list(dict.fromkeys(titles))
    result = await session.scalars(select(Title).where(Title.title.in_(unique_titles)))
    existing = {t.title: t for t in result}

    title_insts = []
    for t in unique_titles:
        if t in existing:
            title_insts.append(existing[t])
        else:
            title_inst = Title(title=t)
            session.add(title_inst)
            title_insts.append(title_inst)

    await session.flush()
    return title_insts

async def list_titles(session: AsyncSession, query: TitleListQuery):
    request_count = _request_count()
    brand_count = _brand_count()
    tier_word_count = _tier_word_count()
    descriptor_count = _descriptor_count()

    SORT_COLUMNS = {
        "id": Title.id,
        "title": Title.title,
        "created_at": Title.created_at,
        "request_count": request_count,
        "brand_count": brand_count,
        "tier_word_count": tier_word_count,
        "descriptor_count": descriptor_count,
        "total_word_count": brand_count + tier_word_count + descriptor_count,
    }
    sort_column = SORT_COLUMNS.get(query.sort, request_count)
    order_clause = sort_column.asc() if query.order == "asc" else sort_column.desc()

    stmt = select(
        Title,
        request_count.label("request_count"),
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


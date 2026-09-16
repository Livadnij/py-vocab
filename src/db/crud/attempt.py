from sqlalchemy import delete, func, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from src.db.models import AttemptError, AttemptStatus, ProcessingAttempt, Prompt, Thinking, Title

async def create_attempt(session: AsyncSession, title_id: int) -> ProcessingAttempt:
    attempt_inst = ProcessingAttempt(title_id=title_id)
    session.add(attempt_inst)
    await session.flush()
    return attempt_inst

async def get_pending_attempts(session: AsyncSession, limit: int | None = None) -> list[ProcessingAttempt]:
    stmt = (
        select(ProcessingAttempt)
        .where(ProcessingAttempt.status == AttemptStatus.pending)
        .options(
            joinedload(ProcessingAttempt.title).selectinload(Title.brands),
            joinedload(ProcessingAttempt.title).selectinload(Title.tier_words),
            joinedload(ProcessingAttempt.title).selectinload(Title.descriptors),
        )
        .order_by(ProcessingAttempt.created_at)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def update_attempt_status(
    session: AsyncSession, attempt_id: int, status: AttemptStatus
) -> None:
    await session.execute(
        update(ProcessingAttempt)
        .where(ProcessingAttempt.id == attempt_id)
        .values(status=status)
    )

async def recover_stuck_attempts(session: AsyncSession) -> int:
    stuck = select(ProcessingAttempt.id).where(
        ProcessingAttempt.status == AttemptStatus.running
    )

    await session.execute(delete(Thinking).where(Thinking.attempt_id.in_(stuck)))
    await session.execute(delete(AttemptError).where(AttemptError.attempt_id.in_(stuck)))

    result = await session.execute(
        update(ProcessingAttempt)
        .where(ProcessingAttempt.status == AttemptStatus.running)
        .values(status=AttemptStatus.pending)
    )
    await session.commit()
    return result.rowcount

async def get_attempts_for_title(session: AsyncSession, title_id: int):
    attempt_error_count = (
        select(func.count(AttemptError.id))
        .where(AttemptError.attempt_id == ProcessingAttempt.id)
        .correlate(ProcessingAttempt)
        .scalar_subquery()
    )

    stmt = (
        select(ProcessingAttempt, attempt_error_count.label("attempt_error_count"))
        .where(ProcessingAttempt.title_id == title_id)
        .order_by(ProcessingAttempt.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.all()


async def get_attempt_detail(session: AsyncSession, attempt_id: int):
    attempt_error_count = (
        select(func.count(AttemptError.id))
        .where(AttemptError.attempt_id == ProcessingAttempt.id)
        .correlate(ProcessingAttempt)
        .scalar_subquery()
    )

    stmt = (
        select(
            ProcessingAttempt,
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
            Prompt.prompt,
        )
        .outerjoin(Thinking, Thinking.attempt_id == ProcessingAttempt.id)
        .outerjoin(Prompt, Prompt.id == Thinking.used_prompt_id)
        .where(ProcessingAttempt.id == attempt_id)
    )
    result = await session.execute(stmt)
    return result.first()
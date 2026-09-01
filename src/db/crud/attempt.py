from sqlalchemy import delete, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from src.db.models import AttemptError, AttemptStatus, ProcessingAttempt, Thinking, Title

async def create_attempt(session: AsyncSession, title_id: int, request_id: int) -> ProcessingAttempt:
    attempt_inst = ProcessingAttempt(title_id=title_id, request_id=request_id)
    session.add(attempt_inst)
    await session.flush()
    return attempt_inst

async def get_pending_attempts_for_request(
    session: AsyncSession, request_id: int
) -> list[ProcessingAttempt]:
    result = await session.execute(
        select(ProcessingAttempt)
        .where(
            ProcessingAttempt.request_id == request_id,
            ProcessingAttempt.status == AttemptStatus.pending,
        )
        .options(
            joinedload(ProcessingAttempt.title).selectinload(Title.brands),
            joinedload(ProcessingAttempt.title).selectinload(Title.tier_words),
            joinedload(ProcessingAttempt.title).selectinload(Title.descriptors),
        )
        .order_by(ProcessingAttempt.created_at)
    )
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
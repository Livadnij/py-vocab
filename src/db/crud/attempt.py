from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from src.db.models import AttemptStatus, ProcessingAttempt, Title

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
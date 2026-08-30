from datetime import timedelta

from sqlalchemy import select, update
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import AttemptStatus, ProcessingAttempt, Request

async def create_request(session: AsyncSession, titles_amount: int) -> Request:
    request_inst = Request(uuid=uuid4(), titles_amount=titles_amount)
    session.add(request_inst)
    await session.flush()
    return request_inst

async def get_next_request_with_pending_attempts(session: AsyncSession) -> Request | None:
    result = await session.execute(
        select(Request)
        .join(ProcessingAttempt)
        .where(ProcessingAttempt.status == AttemptStatus.pending)
        .order_by(Request.created_at)
        .limit(1)
    )
    return result.scalars().first()

async def update_request(
        session: AsyncSession, 
        request_id:int,
        titles_amount: int | None = None,
        elapsed_time: timedelta | None = None,
        ) -> None:
    values = {k: v for k, v in {"titles_amount": titles_amount, "elapsed_time": elapsed_time}.items() if v is not None}
    if not values:
        return
    await session.execute(update(Request).where(Request.id == request_id).values(**values))
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import HardError


async def create_hard_error(session: AsyncSession, message: str) -> HardError:
    hard_error_inst = HardError(message=message)
    session.add(hard_error_inst)
    await session.flush()
    return hard_error_inst

async def get_hard_errors(session: AsyncSession, limit: int, offset: int) -> list[HardError]:
    stmt = (
        select(HardError)
        .order_by(HardError.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.scalars(stmt)
    return list(result.all())

async def count_hard_errors(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(HardError)) or 0
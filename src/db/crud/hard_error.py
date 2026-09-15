from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import HardError


async def create_hard_error(session: AsyncSession, message: str, request_id:int) -> HardError:
    hard_error_inst = HardError(request_id=request_id, message=message)
    session.add(hard_error_inst)
    await session.flush()
    return hard_error_inst

async def get_errors_for_request(session: AsyncSession, request_id: int) -> list[HardError]:
    result = await session.scalars(
        select(HardError).where(HardError.request_id == request_id).order_by(HardError.created_at)
    )
    return list(result.all())
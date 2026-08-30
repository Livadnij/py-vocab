from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import HardError


async def create_hard_error(session: AsyncSession, message: str, request_id:int) -> HardError:
    hard_error_inst = HardError(request_id=request_id, message=message)
    session.add(hard_error_inst)
    await session.flush()
    return hard_error_inst

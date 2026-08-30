from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import AttemptError


async def create_attempt_error(session: AsyncSession, message: str, attempt_id:int) -> AttemptError:
    attempt_error_inst = AttemptError(attempt_id=attempt_id, message=message)
    session.add(attempt_error_inst)
    await session.flush()
    return attempt_error_inst

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import AttemptError


async def create_attempt_error(session: AsyncSession, message: str, attempt_id:int) -> AttemptError:
    attempt_error_inst = AttemptError(attempt_id=attempt_id, message=message)
    session.add(attempt_error_inst)
    await session.flush()
    return attempt_error_inst

async def get_errors_for_attempt(session: AsyncSession, attempt_id: int) -> list[AttemptError]:
    result = await session.scalars(
        select(AttemptError).where(AttemptError.attempt_id == attempt_id).order_by(AttemptError.created_at)
    )
    return list(result.all())
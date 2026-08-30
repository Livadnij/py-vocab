import asyncio

from sqlalchemy import update

from src.config import settings
from src.db.database import Database
from src.db.models import AttemptStatus, ProcessingAttempt


async def reset_all_attempts():
    db = Database(settings.DSN)
    async with db.session() as session:
        result = await session.execute(
            update(ProcessingAttempt).values(status=AttemptStatus.pending)
        )
        await session.commit()
        print(f"Reset {result.rowcount} attempts to pending.")
    await db.close()


if __name__ == "__main__":
    asyncio.run(reset_all_attempts())
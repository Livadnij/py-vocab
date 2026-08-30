from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Thinking
from src.llm.llm import ExtractionResult
from dataclasses import asdict


async def create_thinking(session: AsyncSession, llm_response: ExtractionResult, attempt_id: int) -> Thinking:
    thinking_inst = Thinking(attempt_id=attempt_id, **asdict(llm_response))
    session.add(thinking_inst)
    await session.flush()
    return thinking_inst

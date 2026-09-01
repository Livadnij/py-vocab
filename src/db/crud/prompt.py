from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Prompt, ProcessingAttempt, Thinking


async def get_prompt_by_id(session: AsyncSession, prompt_id: int) -> Prompt | None:
    return await session.get(Prompt, prompt_id)

async def get_default_prompt(session: AsyncSession) -> Prompt | None:
    result = await session.execute(select(Prompt).where(Prompt.is_default.is_(True)))
    return result.scalars().first()

async def create_prompt(session: AsyncSession, prompt: str) -> Prompt:
    prompt_inst = Prompt(prompt=prompt, is_default=False)
    session.add(prompt_inst)
    await session.flush()
    return prompt_inst


def _titles_used_count():
    return (
        select(func.count(func.distinct(ProcessingAttempt.title_id)))
        .join(Thinking, Thinking.attempt_id == ProcessingAttempt.id)
        .where(Thinking.used_prompt_id == Prompt.id)
        .correlate(Prompt)
        .scalar_subquery()
    )


async def list_prompts(session: AsyncSession, limit: int, offset: int):
    titles_used_count = _titles_used_count()
    stmt = (
        select(Prompt, titles_used_count.label("titles_used_count"))
        .order_by(Prompt.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return result.all()


async def count_prompts(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(Prompt)) or 0
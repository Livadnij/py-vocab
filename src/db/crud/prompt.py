from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Prompt, ProcessingAttempt, Thinking
from src.schemas.prompt import PromptListQuery


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

async def set_default_prompt(session: AsyncSession, prompt_id: int) -> Prompt | None:
    prompt = await session.get(Prompt, prompt_id)
    if prompt is None:
        return None
    await session.execute(update(Prompt).where(Prompt.is_default.is_(True)).values(is_default=False))
    prompt.is_default = True
    await session.flush()
    return prompt


def _titles_used_count():
    return (
        select(func.count(func.distinct(ProcessingAttempt.title_id)))
        .join(Thinking, Thinking.attempt_id == ProcessingAttempt.id)
        .where(Thinking.used_prompt_id == Prompt.id)
        .correlate(Prompt)
        .scalar_subquery()
    )


async def get_prompt_out_row(session: AsyncSession, prompt_id: int):
    titles_used_count = _titles_used_count()
    stmt = (
        select(Prompt, titles_used_count.label("titles_used_count"))
        .where(Prompt.id == prompt_id)
    )
    result = await session.execute(stmt)
    return result.first()


async def list_prompts(session: AsyncSession, query: PromptListQuery):
    titles_used_count = _titles_used_count()

    SORT_COLUMNS = {
        "id": Prompt.id,
        "created_at": Prompt.created_at,
        "titles_used_count": titles_used_count,
    }
    sort_column = SORT_COLUMNS.get(query.sort, Prompt.created_at)
    order_clause = sort_column.asc() if query.order == "asc" else sort_column.desc()

    stmt = (
        select(Prompt, titles_used_count.label("titles_used_count"))
        .order_by(order_clause)
        .limit(query.limit)
        .offset(query.offset)
    )
    result = await session.execute(stmt)
    return result.all()


async def count_prompts(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(Prompt)) or 0
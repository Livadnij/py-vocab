from src.db.database import Database
from src.db.crud import prompt as crud_prompt
from src.schemas.common import PaginationOut
from src.schemas.prompt import PromptListOut, PromptListQuery, PromptOut


async def create_prompt(db: Database, prompt: str) -> PromptOut:
    async with db.session() as session:
        prompt_inst = await crud_prompt.create_prompt(session, prompt)
        await session.commit()
        return PromptOut(
            id=prompt_inst.id,
            prompt=prompt_inst.prompt,
            is_default=prompt_inst.is_default,
            created_at=prompt_inst.created_at,
            titles_used_count=0,
        )


async def list_prompts(db: Database, query: PromptListQuery) -> PromptListOut:
    async with db.session() as session:
        rows = await crud_prompt.list_prompts(session, query)
        total = await crud_prompt.count_prompts(session)

    items = [
        PromptOut(
            id=row.Prompt.id,
            prompt=row.Prompt.prompt,
            is_default=row.Prompt.is_default,
            created_at=row.Prompt.created_at,
            titles_used_count=row.titles_used_count,
        )
        for row in rows
    ]
    return PromptListOut(items=items, pagination=PaginationOut(limit=query.limit, offset=query.offset, total=total))


async def set_default_prompt(db: Database, prompt_id: int) -> PromptOut | None:
    async with db.session() as session:
        prompt = await crud_prompt.set_default_prompt(session, prompt_id)
        if prompt is None:
            return None
        await session.commit()
        row = await crud_prompt.get_prompt_out_row(session, prompt_id)

    return PromptOut(
        id=row.Prompt.id,
        prompt=row.Prompt.prompt,
        is_default=row.Prompt.is_default,
        created_at=row.Prompt.created_at,
        titles_used_count=row.titles_used_count,
    )
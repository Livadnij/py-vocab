from src.db.database import Database
from src.db.crud import prompt as crud_prompt
from src.schemas import PaginationOut, PromptListOut, PromptOut


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


async def list_prompts(db: Database, limit: int, offset: int) -> PromptListOut:
    async with db.session() as session:
        rows = await crud_prompt.list_prompts(session, limit, offset)
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
    return PromptListOut(items=items, pagination=PaginationOut(limit=limit, offset=offset, total=total))
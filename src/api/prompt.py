from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.deps import get_db
from src.db.database import Database
from src.schemas.prompt import PromptCreate, PromptListOut, PromptListQuery, PromptOut
from src.service import prompt as service_prompt

router = APIRouter()


@router.post("/prompts", response_model=PromptOut)
async def create_prompt(
    body: PromptCreate,
    db: Annotated[Database, Depends(get_db)],
):
    return await service_prompt.create_prompt(db, body.prompt)


@router.get("/prompts", response_model=PromptListOut)
async def list_prompts(
    db: Annotated[Database, Depends(get_db)],
    query: Annotated[PromptListQuery, Query()],
):
    return await service_prompt.list_prompts(db, query)


@router.post("/prompts/{prompt_id}/set-default", response_model=PromptOut)
async def set_default_prompt(
    db: Annotated[Database, Depends(get_db)],
    prompt_id: int,
):
    result = await service_prompt.set_default_prompt(db, prompt_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return result
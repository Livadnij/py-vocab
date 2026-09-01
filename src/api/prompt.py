from typing import Annotated

from fastapi import APIRouter, Depends, Query
from src.api.deps import get_db
from src.db.database import Database
from src.schemas.common import PaginationParams
from src.schemas import PromptCreate, PromptListOut, PromptOut
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
    query: Annotated[PaginationParams, Query()],
):
    return await service_prompt.list_prompts(db, query.limit, query.offset)
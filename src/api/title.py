from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.deps import get_db
from src.db.database import Database
from src.schemas.title import AttemptOut, TitleBase, TitleCreate, TitleListQuery, TitleListOut, TitleWithAttemptsOut
from src.service import title as service_title

router = APIRouter()


@router.post("/titles", response_model=list[TitleBase])
async def create_titles(
    body: TitleCreate,
    db: Annotated[Database, Depends(get_db)],
):
    return await service_title.create_titles(db, body.titles)

@router.get("/titles", response_model=TitleListOut)
async def list_titles(
    db: Annotated[Database, Depends(get_db)],
    query: Annotated[TitleListQuery, Query()],
):
    return await service_title.list_titles(db, query)

@router.get("/titles/{title_id}", response_model=TitleWithAttemptsOut)
async def get_title_detail(
    db: Annotated[Database, Depends(get_db)],
    title_id: int,
):
    result = await service_title.get_title_detail(db, title_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Title not found")
    return result

@router.post("/titles/{title_id}/attempts", response_model=AttemptOut)
async def retry_title(
    db: Annotated[Database, Depends(get_db)],
    title_id: int,
):
    result = await service_title.retry_title(db, title_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Title not found")
    return result
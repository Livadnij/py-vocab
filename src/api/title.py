from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.deps import get_db
from src.db.database import Database
from src.schemas.title import TitleDetailOut
from src.service import title as service_title

router = APIRouter()


@router.get("/requests/{request_id}/titles/{title_id}", response_model=TitleDetailOut)
async def get_title_by_request(
    db: Annotated[Database, Depends(get_db)],
    request_id: int,
    title_id: int,
):
    result = await service_title.get_title_by_request(db, request_id, title_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Title not found")
    return result
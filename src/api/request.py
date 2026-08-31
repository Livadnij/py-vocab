from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.deps import get_db
from src.db.database import Database
from src.schemas import RequestDetailOut, RequestGetQuery, RequestListOut, RequestListQuery, RequestOut, TitlesList
from src.service import request as service_request

router = APIRouter()

@router.post("/requests", response_model=list[RequestOut])
async def create_requests(
    titles: TitlesList, 
    db: Annotated[Database, Depends(get_db)]
    ):
    return await service_request.create_request(db, titles.titles)


@router.get("/requests", response_model=RequestListOut)
async def list_requests(
    db: Annotated[Database, Depends(get_db)],
    query: Annotated[RequestListQuery, Query()],
):
    return await service_request.list_requests(db, query)

@router.get("/requests/{id}", response_model=RequestDetailOut)
async def get_request(
    db: Annotated[Database, Depends(get_db)],
    id: int,
    query: Annotated[RequestGetQuery, Query()],
):
    result = await service_request.get_request(db, id, query)
    if result is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return result
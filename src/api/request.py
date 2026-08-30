from typing import Annotated

from fastapi import APIRouter, Depends
from src.api.deps import get_db
from src.db.database import Database
from src.schemas import TitlesList
from src.service import request as service_request

router = APIRouter()

@router.post("/requests")
async def create_request(titles: TitlesList, db: Annotated[Database, Depends(get_db)]):
    return await service_request.create_request(db, titles.titles)
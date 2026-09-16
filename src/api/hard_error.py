from typing import Annotated

from fastapi import APIRouter, Depends, Query
from src.api.deps import get_db
from src.db.database import Database
from src.schemas.common import PaginationParams
from src.schemas.hard_error import HardErrorListOut
from src.service import hard_error as service_hard_error

router = APIRouter()


@router.get("/hard-errors", response_model=HardErrorListOut)
async def list_hard_errors(
    db: Annotated[Database, Depends(get_db)],
    query: Annotated[PaginationParams, Query()],
):
    return await service_hard_error.list_hard_errors(db, query.limit, query.offset)
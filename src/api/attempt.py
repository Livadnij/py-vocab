from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from src.api.deps import get_db
from src.db.database import Database
from src.db.models import AttemptStatus
from src.schemas.title import AttemptDetailOut
from src.service import attempt as service_attempt

router = APIRouter()


@router.get("/attempts/{attempt_id}", response_model=AttemptDetailOut)
async def get_attempt_detail(
    db: Annotated[Database, Depends(get_db)],
    attempt_id: int,
    response: Response,
):
    result = await service_attempt.get_attempt_detail(db, attempt_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if result.status in (AttemptStatus.succeeded, AttemptStatus.failed):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

    return result
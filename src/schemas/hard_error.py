from datetime import datetime

from pydantic import BaseModel

from src.schemas.common import PaginationOut


class HardErrorOut(BaseModel):
    id: int
    message: str
    created_at: datetime


class HardErrorListOut(BaseModel):
    items: list[HardErrorOut]
    pagination: PaginationOut
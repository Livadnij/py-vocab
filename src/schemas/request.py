from datetime import datetime, timedelta
import enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from src.schemas.common import PaginationOut, PaginationParams
from src.schemas.title import TitleListOut


class TitlesList(BaseModel):
    titles: list[str]
    prompt_id: int | None = None

class RequestStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"

class RequestListParams(BaseModel):
    status: RequestStatus | None = None
    order: Literal["asc", "desc"] = "asc"
    sort: Literal["created_at", "hard_error_count", "attempt_error_count"] | None = None

class RequestListQuery(PaginationParams, RequestListParams):
    pass

class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: UUID
    titles_amount: int
    elapsed_time: float | None = None
    created_at: datetime
    attempt_error_count: int = 0
    hard_error_count: int = 0
    selected_prompt_id: int | None = None

    @field_validator("elapsed_time", mode="before")
    @classmethod
    def _seconds(cls, v):
        return v.total_seconds() if isinstance(v, timedelta) else v

class RequestListOut(BaseModel):
    items: list[RequestOut]
    pagination: PaginationOut

class RequestDetailOut(RequestOut):
    titles: TitleListOut

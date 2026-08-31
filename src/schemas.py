from datetime import datetime, timedelta
import enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal

from src.db.models import AttemptStatus

class TokenBase(BaseModel):
    token: str = Field(..., max_length=127)
    label: Literal['descriptor', 'brand', 'tier']

    @field_validator('token')
    @classmethod
    def validate_token(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Token can't be empty")
        if " " in v:
            raise ValueError("Token can't contain more than 1 word")
        return v

class PaginationOut(BaseModel):
    limit: int
    offset: int
    total: int

class TokenList(BaseModel):
    tokens: list[TokenBase]

class TitlesList(BaseModel):
    titles: list[str]

class PaginationParams(BaseModel):
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)

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

    @field_validator("elapsed_time", mode="before")
    @classmethod
    def _seconds(cls, v):
        return v.total_seconds() if isinstance(v, timedelta) else v

class RequestListOut(BaseModel):
    items: list[RequestOut]
    pagination: PaginationOut

class RequestGetParams(BaseModel):
    status: AttemptStatus | None = None
    order: Literal["asc", "desc"] = "asc"
    sort: Literal["title", "total_word_count", "tier_word_count", "brand_count", "descriptor_count", "attempt_error_count", "status", "total_tokens" ] | None = None

class RequestGetQuery(PaginationParams, RequestGetParams):
    pass

class TitleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime
    brand_count: int = 0
    tier_word_count: int = 0
    descriptor_count: int = 0
    attempt_error_count: int = 0
    status: AttemptStatus
    total_tokens: int = 0


class TitleListOut(BaseModel):
    items: list[TitleOut]
    pagination: PaginationOut

class RequestDetailOut(RequestOut):
    titles: TitleListOut
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.db.models import AttemptStatus
from src.schemas.common import PaginationOut, PaginationParams
from src.schemas.thinking import ThinkingOut


class TitleCreate(BaseModel):
    titles: list[str] = Field(min_length=1)


class TitleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime


class RequestGetParams(BaseModel):
    status: AttemptStatus | None = None
    order: Literal["asc", "desc"] = "asc"
    sort: Literal["title", "total_word_count", "tier_word_count", "brand_count", "descriptor_count", "attempt_error_count", "status", "total_tokens"] | None = None


class WordWithOccurrence(BaseModel):
    id: int
    name: str
    occurrence: int


class RequestGetQuery(PaginationParams, RequestGetParams):
    pass

class TitleOut(TitleBase):
    status: AttemptStatus
    brand_count: int = 0
    tier_word_count: int = 0
    descriptor_count: int = 0
    attempt_error_count: int = 0
    total_tokens: int = 0
    used_prompt_id: int | None = None
    attempt_id: int | None = None


class TitleDetailOut(TitleBase):
    status: AttemptStatus
    brands: list[WordWithOccurrence] = []
    tier_words: list[WordWithOccurrence] = []
    descriptors: list[WordWithOccurrence] = []
    attempt_error_count: int = 0
    thinking: ThinkingOut | None = None


class TitleListOut(BaseModel):
    items: list[TitleOut]
    pagination: PaginationOut

class TitleListParams(BaseModel):
    q: str | None = None
    order: Literal["asc", "desc"] = "asc"
    sort: Literal["id", "title", "created_at", "request_count", "brand_count", "tier_word_count", "descriptor_count", "total_word_count"] = "request_count"

class TitleListQuery(PaginationParams, TitleListParams):
    pass

class TitleWithRequestsOut(TitleBase):
    brand_count: int = 0
    tier_word_count: int = 0
    descriptor_count: int = 0

class TitleWithRequestsListOut(BaseModel):
    items: list[TitleWithRequestsOut]
    pagination: PaginationOut

class AttemptOut(BaseModel):
    id: int
    request_id: int
    status: AttemptStatus
    created_at: datetime
    attempt_error_count: int = 0

class AttemptErrorOut(BaseModel):
    id: int
    message: str
    created_at: datetime

class AttemptDetailOut(BaseModel):
    id: int
    request_id: int
    status: AttemptStatus
    created_at: datetime
    attempt_error_count: int = 0
    thinking: ThinkingOut | None = None
    prompt: str | None = None
    errors: list[AttemptErrorOut] = []

class TitleWithAttemptsOut(TitleBase):
    brands: list[WordWithOccurrence] = []
    tier_words: list[WordWithOccurrence] = []
    descriptors: list[WordWithOccurrence] = []
    attempts: list[AttemptOut] = []
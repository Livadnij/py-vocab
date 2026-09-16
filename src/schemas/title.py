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


class WordWithOccurrence(BaseModel):
    id: int
    name: str
    occurrence: int


class TitleListParams(BaseModel):
    q: str | None = None
    order: Literal["asc", "desc"] = "asc"
    sort: Literal["id", "title", "created_at", "attempt_count", "brand_count", "tier_word_count", "descriptor_count", "total_word_count"] = "attempt_count"

class TitleListQuery(PaginationParams, TitleListParams):
    pass

class TitleListItemOut(TitleBase):
    brand_count: int = 0
    tier_word_count: int = 0
    descriptor_count: int = 0

class TitleListOut(BaseModel):
    items: list[TitleListItemOut]
    pagination: PaginationOut

class AttemptOut(BaseModel):
    id: int
    status: AttemptStatus
    created_at: datetime
    attempt_error_count: int = 0

class AttemptErrorOut(BaseModel):
    id: int
    message: str
    created_at: datetime

class AttemptDetailOut(BaseModel):
    id: int
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
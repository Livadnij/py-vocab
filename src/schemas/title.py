from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from src.db.models import AttemptStatus
from src.schemas.common import PaginationOut, PaginationParams
from src.schemas.thinking import ThinkingOut


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


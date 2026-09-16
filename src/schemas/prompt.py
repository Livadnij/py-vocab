from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.common import PaginationOut, PaginationParams


class PromptCreate(BaseModel):
    prompt: str = Field(..., min_length=1)


class PromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    is_default: bool
    created_at: datetime
    titles_used_count: int = 0


class PromptListOut(BaseModel):
    items: list[PromptOut]
    pagination: PaginationOut


class PromptListParams(BaseModel):
    order: Literal["asc", "desc"] = "desc"
    sort: Literal["id", "created_at", "titles_used_count"] = "created_at"

class PromptListQuery(PaginationParams, PromptListParams):
    pass
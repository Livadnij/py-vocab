from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.common import PaginationOut


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
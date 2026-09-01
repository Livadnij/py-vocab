from datetime import timedelta
from pydantic import BaseModel, ConfigDict, field_validator


class ThinkingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    used_prompt_id: int
    model: str
    finish_reason: str
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int | None = None
    duration: float
    text: str | None = None
    response: str | None = None

    @field_validator("duration", mode="before")
    @classmethod
    def _seconds(cls, v):
        return v.total_seconds() if isinstance(v, timedelta) else v
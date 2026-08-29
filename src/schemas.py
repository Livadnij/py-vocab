from pydantic import BaseModel, Field, field_validator
from typing import Literal

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

class TokenList(BaseModel):
    tokens: list[TokenBase]

class TitlesList(BaseModel):
    titles: list[str]
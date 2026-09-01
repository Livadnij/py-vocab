from pydantic import BaseModel, Field

class PaginationOut(BaseModel):
    limit: int
    offset: int
    total: int

class PaginationParams(BaseModel):
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
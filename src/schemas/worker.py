from pydantic import BaseModel


class ProcessAttemptsBody(BaseModel):
    limit: int | None = None
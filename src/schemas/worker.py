from pydantic import BaseModel


class ProcessRequestsBody(BaseModel):
    request_ids: list[int]
from uuid import uuid4
from sqlalchemy.orm import Session
from src.db.models import Request

def create_request(session: Session, titles_amount: int) -> Request:
    request_inst = Request(uuid=uuid4(), titles_amount=titles_amount)
    session.add(request_inst)
    session.flush()
    return request_inst
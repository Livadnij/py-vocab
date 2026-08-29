from sqlalchemy.orm import Session
from src.db.models import ProcessingAttempt

def create_attempt(session: Session, title_id: int, request_id: int) -> ProcessingAttempt:
    attempt_inst = ProcessingAttempt(title_id=title_id, request_id=request_id)
    session.add(attempt_inst)
    session.flush()
    return attempt_inst
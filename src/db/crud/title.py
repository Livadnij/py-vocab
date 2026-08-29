from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import Title

def create_title(session: Session, title: str, request_id: int) -> Title:
    title_inst = Title(title=title, request_id=request_id)
    session.add(title_inst)
    session.flush()
    return title_inst

def get_existing_titles(session: Session, titles: list[str]) -> set[str]:
    return set(session.scalars(select(Title.title).where(Title.title.in_(titles))))
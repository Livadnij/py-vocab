from src.db.database import Database
from src.db.crud import request as crud_request, title as crud_title, attempt as crud_attempt

def create_request(db: Database, titles: list[str]):
    with db.session() as session:
        existing = crud_title.get_existing_titles(session, titles)
        new_titles = [t for t in titles if t not in existing]

        request_inst = crud_request.create_request(session, titles_amount=len(new_titles))

        for t in new_titles:
            title_inst = crud_title.create_title(session, title=t, request_id=request_inst.id)
            crud_attempt.create_attempt(session, title_id=title_inst.id, request_id=request_inst.id)

        session.commit()
        return request_inst
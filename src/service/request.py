from src.db.database import Database
from src.db.crud import request as crud_request, title as crud_title, attempt as crud_attempt


CHUNK_SIZE = 200

async def create_request(db: Database, titles: list[str]):
    unique_titles = list(dict.fromkeys(titles))  # order-preserving dedup

    async with db.session() as session:
        existing = await crud_title.get_titles_by_title(session, unique_titles)
        new_titles = [t for t in unique_titles if t not in existing]

        requests = []
        for i in range(0, len(new_titles), CHUNK_SIZE):
            chunk = new_titles[i:i + CHUNK_SIZE]
            request_inst = await crud_request.create_request(session, titles_amount=len(chunk))

            for t in chunk:
                title_inst = await crud_title.create_title(session, title=t, request_id=request_inst.id)
                await crud_attempt.create_attempt(session, title_id=title_inst.id, request_id=request_inst.id)

            requests.append(request_inst)

        await session.commit()
        return requests
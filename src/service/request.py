from fastapi import HTTPException

from src.db.database import Database
from src.db.crud import (
    request as crud_request, 
    title as crud_title, 
    attempt as crud_attempt,
    prompt as crud_prompt
    )
from src.schemas import PaginationOut, RequestDetailOut, RequestGetQuery, RequestListOut, RequestListQuery, RequestOut, TitleListOut, TitleOut


CHUNK_SIZE = 200

async def create_request(db: Database, titles: list[str], prompt_id: int | None = None):
    unique_titles = list(dict.fromkeys(titles))

    async with db.session() as session:
        if prompt_id is not None:
            prompt = await crud_prompt.get_prompt_by_id(session, prompt_id)
            if prompt is None:
                raise HTTPException(status_code=404, detail="Prompt not found")
        existing = await crud_title.get_titles_by_title(session, unique_titles)
        new_titles = [t for t in unique_titles if t not in existing]

        requests = []
        for i in range(0, len(new_titles), CHUNK_SIZE):
            chunk = new_titles[i:i + CHUNK_SIZE]
            request_inst = await crud_request.create_request(session, titles_amount=len(chunk), selected_prompt_id=prompt_id)

            for t in chunk:
                title_inst = await crud_title.create_title(session, title=t, request_id=request_inst.id)
                await crud_attempt.create_attempt(session, title_id=title_inst.id, request_id=request_inst.id)

            requests.append(request_inst)

        await session.commit()
        return requests

async def list_requests(db: Database, query: RequestListQuery) -> RequestListOut:
    async with db.session() as session:
        rows = await crud_request.list_requests(session, query)
        total = await crud_request.count_requests(session, query)

    items = [
        RequestOut(
            id=row.Request.id,
            uuid=row.Request.uuid,
            titles_amount=row.Request.titles_amount,
            elapsed_time=row.Request.elapsed_time,
            created_at=row.Request.created_at,
            attempt_error_count=row.attempt_error_count,
            hard_error_count=row.hard_error_count,
            selected_prompt_id=row.Request.selected_prompt_id
        )
        for row in rows
    ]
    return RequestListOut(
        items=items,
        pagination=PaginationOut(limit=query.limit, offset=query.offset, total=total),
    )

async def get_request(db: Database, id: int, query: RequestGetQuery) -> RequestDetailOut | None:
    async with db.session() as session:
        row = await crud_request.get_request_by_id(session, id)
        if row is None:
            return None
        title_rows = await crud_title.list_titles_for_request(session, id, query)
        total = await crud_title.count_titles_for_request(session, id, query)

    request_inst = row.Request
    titles = [
        TitleOut(
            id=r.Title.id,
            title=r.Title.title,
            created_at=r.Title.created_at,
            brand_count=r.brand_count,
            tier_word_count=r.tier_word_count,
            descriptor_count=r.descriptor_count,
            attempt_error_count=r.attempt_error_count,
            status=r.status,
            total_tokens=r.total_tokens,
            used_prompt_id=r.used_prompt_id
        )
        for r in title_rows
    ]

    return RequestDetailOut(
        id=request_inst.id,
        uuid=request_inst.uuid,
        titles_amount=request_inst.titles_amount,
        elapsed_time=request_inst.elapsed_time,
        created_at=request_inst.created_at,
        attempt_error_count=row.attempt_error_count,
        hard_error_count=row.hard_error_count,
        selected_prompt_id=row.Request.selected_prompt_id,
        titles=TitleListOut(
            items=titles,
            pagination=PaginationOut(limit=query.limit, offset=query.offset, total=total),
        ),
    )
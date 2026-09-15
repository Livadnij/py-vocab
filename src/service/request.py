from fastapi import HTTPException

from src.db.database import Database
from src.db.crud import (
    request as crud_request,
    title as crud_title,
    attempt as crud_attempt,
    prompt as crud_prompt,
    hard_error as crud_hard_error,
    )
from src.schemas.common import PaginationOut
from src.schemas.request import HardErrorOut, RequestDetailOut, RequestListOut, RequestListQuery, RequestOut
from src.schemas.title import RequestGetQuery, TitleListOut, TitleOut


async def create_request(db: Database, title_ids: list[int], prompt_id: int | None = None) -> RequestOut:
    unique_ids = list(dict.fromkeys(title_ids))

    async with db.session() as session:
        if prompt_id is not None:
            prompt = await crud_prompt.get_prompt_by_id(session, prompt_id)
            if prompt is None:
                raise HTTPException(status_code=404, detail="Prompt not found")

        request_inst = await crud_request.create_request(
            session, titles_amount=len(unique_ids), selected_prompt_id=prompt_id
        )

        titles = await crud_title.get_titles_by_ids(session, unique_ids)
        found_ids = {t.id for t in titles}
        missing_ids = [i for i in unique_ids if i not in found_ids]

        if missing_ids:
            await crud_hard_error.create_hard_error(
                session,
                request_id=request_inst.id,
                message=f"Title ids not found: {missing_ids}",
            )
            await session.commit()
            raise HTTPException(status_code=404, detail=f"Title ids not found: {missing_ids}")

        for title_inst in titles:
            await crud_attempt.create_attempt(session, title_id=title_inst.id, request_id=request_inst.id)

        await session.commit()

        return RequestOut(
            id=request_inst.id,
            uuid=request_inst.uuid,
            titles_amount=request_inst.titles_amount,
            elapsed_time=request_inst.elapsed_time,
            created_at=request_inst.created_at,
            attempt_error_count=0,
            hard_error_count=0,
            selected_prompt_id=request_inst.selected_prompt_id,
        )

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
        hard_error_rows = await crud_hard_error.get_errors_for_request(session, id)

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
            used_prompt_id=r.used_prompt_id,
            attempt_id=r.attempt_id,
        )
        for r in title_rows
    ]

    hard_errors = [
        HardErrorOut(id=e.id, message=e.message, created_at=e.created_at)
        for e in hard_error_rows
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
        hard_errors=hard_errors,
    )
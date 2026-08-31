from datetime import timedelta

from sqlalchemy import and_, exists, func, not_, or_, select, update
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import AttemptError, AttemptStatus, HardError, ProcessingAttempt, Request
from src.schemas import RequestListQuery, RequestStatus


async def create_request(session: AsyncSession, titles_amount: int) -> Request:
    request_inst = Request(uuid=uuid4(), titles_amount=titles_amount)
    session.add(request_inst)
    await session.flush()
    return request_inst

async def get_next_request_with_pending_attempts(session: AsyncSession) -> Request | None:
    result = await session.execute(
        select(Request)
        .join(ProcessingAttempt)
        .where(ProcessingAttempt.status == AttemptStatus.pending)
        .order_by(Request.created_at)
        .limit(1)
    )
    return result.scalars().first()

async def update_request(
        session: AsyncSession,
        request_id:int,
        titles_amount: int | None = None,
        elapsed_time: timedelta | None = None,
        ) -> None:
    values = {k: v for k, v in {"titles_amount": titles_amount, "elapsed_time": elapsed_time}.items() if v is not None}
    if not values:
        return
    await session.execute(update(Request).where(Request.id == request_id).values(**values))


def _request_has_attempt_status(status: AttemptStatus):
    return exists().where(
        ProcessingAttempt.request_id == Request.id,
        ProcessingAttempt.status == status,
    )

def _has_hard_error():
    return exists().where(HardError.request_id == Request.id)

def _hard_error_count():
    return (
        select(func.count(HardError.id))
        .where(HardError.request_id == Request.id)
        .correlate(Request)
        .scalar_subquery()
    )

def _request_attempt_error_count():
    return (
        select(func.count(AttemptError.id))
        .join(ProcessingAttempt, AttemptError.attempt_id == ProcessingAttempt.id)
        .where(ProcessingAttempt.request_id == Request.id)
        .correlate(Request)
        .scalar_subquery()
    )

STATUS_CONDITIONS = {
    RequestStatus.pending: lambda: not_(or_(
        _request_has_attempt_status(AttemptStatus.succeeded),
        _request_has_attempt_status(AttemptStatus.running),
        _request_has_attempt_status(AttemptStatus.failed),
    )),
    RequestStatus.running: lambda: _request_has_attempt_status(AttemptStatus.running),
    RequestStatus.succeeded: lambda: and_(
        not_(_request_has_attempt_status(AttemptStatus.pending)),
        not_(_request_has_attempt_status(AttemptStatus.running)),
        not_(_has_hard_error()),
    ),
    RequestStatus.failed: lambda: _has_hard_error(),
}


async def list_requests(session: AsyncSession, query: RequestListQuery):
    hard_error_count = _hard_error_count()
    attempt_error_count = _request_attempt_error_count()

    SORT_COLUMNS = {
        "created_at": Request.created_at,
        "hard_error_count": hard_error_count,
        "attempt_error_count": attempt_error_count,
    }

    sort_column = SORT_COLUMNS.get(query.sort, Request.created_at)
    order_clause = sort_column.asc() if query.order == "asc" else sort_column.desc()

    stmt = select(
        Request,
        hard_error_count.label("hard_error_count"),
        attempt_error_count.label("attempt_error_count"),
    )
    if query.status is not None:
        stmt = stmt.where(STATUS_CONDITIONS[query.status]())

    stmt = stmt.order_by(order_clause).limit(query.limit).offset(query.offset)

    result = await session.execute(stmt)
    return result.all()


async def count_requests(session: AsyncSession, query: RequestListQuery) -> int:
    stmt = select(func.count()).select_from(Request)
    if query.status is not None:
        stmt = stmt.where(STATUS_CONDITIONS[query.status]())
    return await session.scalar(stmt) or 0

async def get_request_by_id(session: AsyncSession, request_id: int):
    stmt = select(
        Request,
        _hard_error_count().label("hard_error_count"),
        _request_attempt_error_count().label("attempt_error_count"),
    ).where(Request.id == request_id)
    result = await session.execute(stmt)
    return result.first()
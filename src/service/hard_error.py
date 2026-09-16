from src.db.database import Database
from src.db.crud import hard_error as crud_hard_error
from src.schemas.common import PaginationOut
from src.schemas.hard_error import HardErrorListOut, HardErrorOut


async def list_hard_errors(db: Database, limit: int, offset: int) -> HardErrorListOut:
    async with db.session() as session:
        rows = await crud_hard_error.get_hard_errors(session, limit, offset)
        total = await crud_hard_error.count_hard_errors(session)

    items = [
        HardErrorOut(id=e.id, message=e.message, created_at=e.created_at)
        for e in rows
    ]
    return HardErrorListOut(items=items, pagination=PaginationOut(limit=limit, offset=offset, total=total))
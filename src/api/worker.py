import asyncio
from http.client import HTTPException
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from src.api.deps import get_db, get_llm
from src.db.database import Database
from src.llm.llm import LLLM
from src.schemas.worker import ProcessRequestsBody
from src.worker.loop import process_requests
from src.worker.state import WorkerState

router = APIRouter()

def get_worker_state(request: Request) -> WorkerState:
    return request.state.worker_state

@router.post("/worker/process")
async def process_request_by_id(
    body: ProcessRequestsBody,
    state: Annotated[WorkerState, Depends(get_worker_state)],
    db: Annotated[Database, Depends(get_db)],
    llm: Annotated[LLLM, Depends(get_llm)],
):
    if state.is_processing:
        raise HTTPException(status_code=409, detail="Worker is already processing")

    task = asyncio.create_task(process_requests(db, llm, body.request_ids, state))
    state.task = task
    return {"processing": body.request_ids}


@router.post("/worker/stop")
async def stop_worker(state: Annotated[WorkerState, Depends(get_worker_state)]):
    if state.task is not None:
        state.task.cancel()
    return {"running": False}

@router.get("/worker/status")
async def worker_status(state: Annotated[WorkerState, Depends(get_worker_state)]):
    return {"processing": state.is_processing}
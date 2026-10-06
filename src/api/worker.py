import asyncio
import json
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from src.api.deps import get_db, get_llm
from src.db.database import Database
from src.llm.llm import LLLM
from src.schemas.worker import ProcessAttemptsBody
from src.worker.loop import process_pending
from src.worker.state import WorkerState

router = APIRouter()

def get_worker_state(request: Request) -> WorkerState:
    return request.state.worker_state

@router.post("/worker/process")
async def process_pending_attempts(
    body: ProcessAttemptsBody,
    state: Annotated[WorkerState, Depends(get_worker_state)],
    db: Annotated[Database, Depends(get_db)],
    llm: Annotated[LLLM, Depends(get_llm)],
):
    if state.is_processing:
        raise HTTPException(status_code=409, detail="Worker is already processing")

    task = asyncio.create_task(process_pending(db, llm, state, body.limit))
    state.task = task
    return {"processing": True, "limit": body.limit}


@router.post("/worker/stop")
async def stop_worker(state: Annotated[WorkerState, Depends(get_worker_state)]):
    if state.task is not None:
        state.task.cancel()
    return {"running": False}

@router.get("/worker/status")
async def worker_status(state: Annotated[WorkerState, Depends(get_worker_state)]):
    return {"processing": state.is_processing}


@router.get("/worker/events")
async def worker_events(state: Annotated[WorkerState, Depends(get_worker_state)]):
    async def event_stream():
        queue = state.subscribe()
        try:
            yield f"data: {json.dumps({'processing': state.is_processing})}\n\n"
            while True:
                payload = await queue.get()
                yield f"data: {json.dumps(payload)}\n\n"
        finally:
            state.unsubscribe(queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
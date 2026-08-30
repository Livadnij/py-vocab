from typing import Annotated
from fastapi import APIRouter, Depends, Request
from src.worker.state import WorkerState

router = APIRouter()

def get_worker_state(request: Request) -> WorkerState:
    return request.state.worker_state

@router.post("/worker/start")
async def start_worker(state: Annotated[WorkerState, Depends(get_worker_state)]):
    state.enabled.set()
    return {"running": True}

@router.post("/worker/stop")
async def stop_worker(state: Annotated[WorkerState, Depends(get_worker_state)]):
    state.enabled.clear()
    return {"running": False}

@router.get("/worker/status")
async def worker_status(state: Annotated[WorkerState, Depends(get_worker_state)]):
    return {"running": state.enabled.is_set(), "processing": state.is_processing}
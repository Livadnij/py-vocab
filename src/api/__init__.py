from fastapi import APIRouter
from src.api.general import router as general_router
from src.api.worker import router as worker_router
from src.api.title import router as title_router
from src.api.prompt import router as prompt_router
from src.api.attempt import router as attempt_router
from src.api.hard_error import router as hard_error_router

router = APIRouter()
router.include_router(general_router, tags=['general'])
router.include_router(worker_router, tags=['worker'])
router.include_router(title_router, tags=['title'])
router.include_router(prompt_router, tags=['prompt'])
router.include_router(attempt_router, tags=['attempt'])
router.include_router(hard_error_router, tags=['hard_error'])
from fastapi import APIRouter
from src.api.general import router as general_router
from src.api.request import router as request_router

router = APIRouter()
router.include_router(general_router)
router.include_router(request_router)
from fastapi import Response, APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return Response(status_code=200)
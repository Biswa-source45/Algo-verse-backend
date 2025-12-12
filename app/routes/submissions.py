# Submissions route placeholder
from fastapi import APIRouter

router = APIRouter(prefix="/submissions", tags=["Submissions"])

@router.get("/")
async def list_submissions():
    return []

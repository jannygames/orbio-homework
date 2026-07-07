from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health", summary="Health check")
async def health() -> dict[str, str]:
    return {"status": "ok"}

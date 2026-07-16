from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse[dict[str, str]])
async def health_check() -> ApiResponse[dict[str, str]]:
    return ApiResponse(
        data={
            "status": "ok",
            "service": "reportflow-api",
            "version": "0.1.0",
        }
    )

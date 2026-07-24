from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import ai, auth, files, health, ocr, reports, templates

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

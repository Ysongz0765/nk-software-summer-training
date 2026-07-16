from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from app.core.config import get_settings
from app.core.exceptions import ResourceNotFoundError, UnsupportedFileTypeError
from app.schemas.common import ApiResponse

router = APIRouter()
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf", ".docx", ".xlsx", ".txt"}


@router.post("/upload", response_model=ApiResponse[dict[str, str]])
async def upload_file(file: Annotated[UploadFile, File(...)]) -> ApiResponse[dict[str, str]]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise UnsupportedFileTypeError()

    settings = get_settings()
    storage_dir = Path(settings.storage_root) / "uploads"
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    target = storage_dir / stored_name
    content = await file.read()
    target.write_bytes(content)

    return ApiResponse(
        data={
            "file_id": stored_name,
            "original_name": file.filename or stored_name,
            "stored_name": stored_name,
        }
    )


@router.get("/{file_id}", response_model=ApiResponse[dict[str, str]])
async def get_file(file_id: str) -> ApiResponse[dict[str, str]]:
    settings = get_settings()
    file_path = Path(settings.storage_root) / "uploads" / file_id
    if not file_path.exists():
        raise ResourceNotFoundError()
    return ApiResponse(
        data={
            "file_id": file_id,
            "path": str(file_path),
        }
    )

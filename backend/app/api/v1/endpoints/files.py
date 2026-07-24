from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError, UnsupportedFileTypeError
from app.models.file import UploadedFile
from app.models.user import User
from app.schemas.common import ApiResponse

router = APIRouter()
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf", ".docx", ".xlsx", ".txt"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@router.post("/upload", response_model=ApiResponse[dict[str, object]])
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[dict[str, object]]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise UnsupportedFileTypeError()

    settings = get_settings()
    storage_dir = Path(settings.storage_root) / "uploads"
    storage_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    target = storage_dir / stored_name
    content = await file.read()
    if not content:
        raise UnsupportedFileTypeError("empty file")
    if len(content) > MAX_UPLOAD_BYTES:
        raise UnsupportedFileTypeError("file size exceeds 20MB")
    target.write_bytes(content)

    record = UploadedFile(
        user_id=current_user.id if current_user else None,
        original_name=file.filename or stored_name,
        stored_name=stored_name,
        file_type=suffix.removeprefix("."),
        file_size=len(content),
        storage_path=str(target),
        status="uploaded",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ApiResponse(
        data={
            "id": record.id,
            "file_id": stored_name,
            "record_id": record.id,
            "original_name": record.original_name,
            "stored_name": stored_name,
            "file_type": record.file_type,
            "file_size": record.file_size,
            "storage_path": record.storage_path,
        }
    )


@router.get("/{file_id}", response_model=ApiResponse[dict[str, object]])
async def get_file(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[dict[str, object]]:
    settings = get_settings()
    record = _get_file_record(file_id, db)
    stored_name = record.stored_name if record else file_id
    file_path = Path(settings.storage_root) / "uploads" / stored_name
    if not file_path.exists():
        raise ResourceNotFoundError()
    return ApiResponse(
        data={
            "id": record.id if record else None,
            "file_id": stored_name,
            "record_id": record.id if record else None,
            "original_name": record.original_name if record else stored_name,
            "stored_name": stored_name,
            "path": str(file_path),
            "file_size": record.file_size if record else file_path.stat().st_size,
        }
    )


def _get_file_record(file_id: str, db: Session) -> UploadedFile | None:
    if file_id.isdigit():
        record = db.get(UploadedFile, int(file_id))
        if record is not None:
            return record
    return db.query(UploadedFile).filter(UploadedFile.stored_name == file_id).one_or_none()

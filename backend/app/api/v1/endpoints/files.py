from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError, UnsupportedFileTypeError
from app.models.file import UploadedFile
from app.models.user import User
from app.schemas.common import ApiResponse
from app.services.file_text import extract_file_text
from app.services.project_context import ensure_project_access, touch_project

router = APIRouter()
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf", ".docx", ".xlsx", ".txt"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@router.post("/upload", response_model=ApiResponse[dict[str, object]])
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
    project_id: Annotated[int | None, Form()] = None,
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

    project = None
    if project_id is not None:
        project = ensure_project_access(db, project_id, current_user)

    record = UploadedFile(
        user_id=current_user.id if current_user else None,
        project_id=project.id if project else None,
        original_name=file.filename or stored_name,
        stored_name=stored_name,
        file_type=suffix.removeprefix("."),
        file_size=len(content),
        storage_path=str(target),
        status="uploaded",
    )
    db.add(record)
    if project is not None:
        touch_project(db, project, commit=False)
    db.commit()
    db.refresh(record)

    return ApiResponse(
        data={
            "id": record.id,
            "file_id": stored_name,
            "record_id": record.id,
            "original_name": record.original_name,
            "stored_name": stored_name,
            "project_id": record.project_id,
            "file_type": record.file_type,
            "file_size": record.file_size,
            "storage_path": record.storage_path,
        }
    )


@router.get("/{file_id}/text", response_model=ApiResponse[dict[str, object]])
async def get_file_text(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[dict[str, object]]:
    settings = get_settings()
    record = _get_file_record(file_id, db)
    _ensure_file_access(record, db, current_user)
    stored_name = record.stored_name if record else file_id
    file_path = Path(settings.storage_root) / "uploads" / stored_name
    if not file_path.exists():
        raise ResourceNotFoundError()
    text = extract_file_text(file_path)
    return ApiResponse(
        data={
            "file_id": stored_name,
            "record_id": record.id if record else None,
            "original_name": record.original_name if record else stored_name,
            "file_type": file_path.suffix.lower().removeprefix("."),
            "text": text,
        }
    )


@router.get("/{file_id}", response_model=ApiResponse[dict[str, object]])
async def get_file(
    file_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[dict[str, object]]:
    settings = get_settings()
    record = _get_file_record(file_id, db)
    _ensure_file_access(record, db, current_user)
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
            "project_id": record.project_id if record else None,
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


def _ensure_file_access(
    record: UploadedFile | None,
    db: Session,
    current_user: User | None,
) -> None:
    if record is None:
        return
    if record.project_id is not None:
        ensure_project_access(db, record.project_id, current_user)
        return
    if current_user is not None and record.user_id not in {None, current_user.id}:
        raise ResourceNotFoundError()

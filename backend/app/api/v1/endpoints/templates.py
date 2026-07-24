from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.models.file import UploadedFile
from app.models.template import Template
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.report import TemplateParseResult
from app.schemas.template import TemplateCreate, TemplateRead
from app.services.template.docx import DocxTemplateService

router = APIRouter()
template_service = DocxTemplateService()


@router.post("", response_model=ApiResponse[TemplateRead])
async def create_template(
    payload: TemplateCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[TemplateRead]:
    file_record = _resolve_file_record(payload, db)
    field_config = dict(payload.field_config)

    if file_record is not None and file_record.stored_name.lower().endswith(".docx"):
        parse_result = await _parse_template_path(file_record.stored_name)
        field_config.setdefault("fields", parse_result.fields)
        field_config.setdefault("parse", parse_result.model_dump(mode="json"))

    template = Template(
        user_id=current_user.id if current_user else None,
        name=payload.name.strip(),
        description=payload.description,
        template_type=payload.template_type,
        file_id=file_record.id if file_record else payload.file_id,
        field_config=field_config,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return ApiResponse(data=_template_read(template))


@router.get("", response_model=ApiResponse[list[TemplateRead]])
async def list_templates(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[list[TemplateRead]]:
    _ensure_default_templates(db)
    query = db.query(Template)
    if current_user is not None:
        query = query.filter((Template.user_id.is_(None)) | (Template.user_id == current_user.id))
    templates = query.order_by(Template.user_id.is_not(None), Template.id).all()
    return ApiResponse(data=[_template_read(template) for template in templates])


@router.get("/{template_id}", response_model=ApiResponse[TemplateRead])
async def get_template(
    template_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[TemplateRead]:
    template = db.get(Template, template_id)
    if template is None:
        raise ResourceNotFoundError()
    return ApiResponse(data=_template_read(template))


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[dict[str, int]],
)
async def delete_template(
    template_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[dict[str, int]]:
    template = db.get(Template, template_id)
    if template is None:
        raise ResourceNotFoundError()
    if template.user_id is None and template.file_id is None:
        raise ResourceNotFoundError("default templates cannot be deleted")
    db.delete(template)
    db.commit()
    return ApiResponse(data={"id": template_id})


@router.post("/parse", response_model=ApiResponse[TemplateParseResult])
async def parse_template(payload: dict[str, str]) -> ApiResponse[TemplateParseResult]:
    result = await _parse_template_path(payload["file_path"])
    return ApiResponse(data=result)


def _resolve_file_record(payload: TemplateCreate, db: Session) -> UploadedFile | None:
    if payload.file_id is not None:
        record = db.get(UploadedFile, payload.file_id)
        if record is None:
            raise ResourceNotFoundError("template file not found")
        return record

    if payload.file_path:
        stored_name = Path(payload.file_path).name
        record = (
            db.query(UploadedFile)
            .filter(UploadedFile.stored_name == stored_name)
            .one_or_none()
        )
        if record is not None:
            return record
    return None


async def _parse_template_path(file_path: str) -> TemplateParseResult:
    actual_path = _resolve_template_path(file_path)
    return await template_service.parse_template(str(actual_path))


def _resolve_template_path(file_path: str) -> Path:
    settings = get_settings()
    storage_root = Path(settings.storage_root).resolve()
    raw_path = Path(file_path)
    candidates = [raw_path] if raw_path.is_absolute() else [
        storage_root / "uploads" / raw_path.name,
        storage_root / "templates" / raw_path.name,
        storage_root / raw_path,
    ]

    for candidate in candidates:
        resolved = candidate.resolve()
        if _is_relative_to(resolved, storage_root) and resolved.exists():
            return resolved
    raise ResourceNotFoundError(f"template file not found: {file_path}")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _ensure_default_templates(db: Session) -> None:
    existing = (
        db.query(Template)
        .filter(Template.user_id.is_(None), Template.file_id.is_(None))
        .count()
    )
    if existing:
        return

    defaults = [
        Template(
            name="默认日报模板",
            description="适合每日工作进展、问题和下一步计划。",
            template_type="daily",
            field_config={
                "fields": [
                    "title",
                    "date",
                    "summary",
                    "completed_tasks",
                    "in_progress_tasks",
                    "problems",
                    "solutions",
                    "next_plan",
                ]
            },
        ),
        Template(
            name="默认周报模板",
            description="适合每周工作总结、风险和下周计划。",
            template_type="weekly",
            field_config={
                "fields": [
                    "title",
                    "date",
                    "summary",
                    "completed_tasks",
                    "in_progress_tasks",
                    "problems",
                    "solutions",
                    "next_plan",
                ]
            },
        ),
    ]
    db.add_all(defaults)
    db.commit()


def _template_read(template: Template) -> TemplateRead:
    return TemplateRead(
        id=template.id,
        user_id=template.user_id,
        name=template.name,
        description=template.description,
        template_type=template.template_type,
        file_id=template.file_id,
        field_config=template.field_config or {},
        created_at=template.created_at,
        updated_at=template.updated_at,
    )

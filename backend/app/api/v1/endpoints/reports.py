from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.core.database import get_db
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.report import Report, ReportVersion
from app.models.user import User
from app.repositories.report import ReportRepository
from app.schemas.common import ApiResponse
from app.schemas.report import (
    ExportResult,
    ReportContent,
    ReportCreate,
    ReportRead,
    ReportSummary,
    ReportUpdate,
    ReportVersionRead,
)
from app.services.export.base import ExportService
from app.services.export.excel import ExcelExportService
from app.services.export.mock import MockExportService
from app.services.export.pdf import PdfExportService
from app.services.export.template_excel import TemplateExcelExportService
from app.services.export.template_word import TemplateWordExportService
from app.services.export.word import WordExportService
from app.services.template.context import (
    load_template_context,
    template_file_path,
    template_render_text,
)
from app.services.template.render import render_template_text

router = APIRouter()
mock_export_service = MockExportService()
word_export_service = WordExportService()
template_word_export_service = TemplateWordExportService()
template_excel_export_service = TemplateExcelExportService()
excel_export_service = ExcelExportService()
pdf_export_service = PdfExportService()


@router.post("", response_model=ApiResponse[ReportRead])
async def create_report(
    payload: ReportCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[ReportRead]:
    repository = ReportRepository(db)
    content = _build_initial_report_content(payload)
    template_context = load_template_context(
        db,
        payload.template_id,
        current_user.id if current_user else None,
    )
    if template_context and template_context.render_text:
        content = _content_with_rendered_text(content, template_context.render_text)
    report = repository.create(
        Report(
            user_id=current_user.id if current_user else None,
            template_id=payload.template_id,
            report_type=payload.report_type,
            title=payload.title,
            report_date=payload.report_date,
            status="draft",
            content=content.model_dump(mode="json"),
            source_data=payload.source_data,
        )
    )
    repository.create_version(
        report_id=report.id,
        content=content.model_dump(mode="json"),
        change_note="initial version",
    )
    return ApiResponse(data=_report_read(report))


@router.get("", response_model=ApiResponse[list[ReportSummary]])
async def list_reports(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[list[ReportSummary]]:
    repository = ReportRepository(db)
    reports = repository.list_reports(user_id=current_user.id if current_user else None)
    return ApiResponse(data=[_report_summary(report) for report in reports])


@router.get("/{report_id}", response_model=ApiResponse[ReportRead])
async def get_report(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[ReportRead]:
    report = _load_report(report_id, db)
    _ensure_report_access(report, current_user)
    return ApiResponse(data=_report_read(report))


@router.put("/{report_id}", response_model=ApiResponse[ReportRead])
async def update_report(
    report_id: int,
    payload: ReportUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[ReportRead]:
    repository = ReportRepository(db)
    report = _load_report(report_id, db)
    _ensure_report_access(report, current_user)

    if payload.title is not None:
        report.title = payload.title
    if payload.status is not None:
        report.status = payload.status
    if payload.source_data is not None:
        report.source_data = payload.source_data
    if payload.content is not None:
        content = _content_with_rendered_template(payload.content, report)
        report.content = content.model_dump(mode="json")
        report.report_type = content.report_type
        report.title = payload.title or payload.content.title
        report.report_date = content.date

    report = repository.save(report)
    if payload.content is not None:
        repository.create_version(
            report_id=report.id,
            content=_report_content(report).model_dump(mode="json"),
            change_note="saved from editor",
        )
    return ApiResponse(data=_report_read(report))


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[dict[str, int]],
)
async def delete_report(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[dict[str, int]]:
    repository = ReportRepository(db)
    report = _load_report(report_id, db)
    _ensure_report_access(report, current_user)
    repository.delete(report)
    return ApiResponse(data={"id": report_id})


@router.post("/{report_id}/versions", response_model=ApiResponse[ReportVersionRead])
async def create_version(
    report_id: int,
    payload: ReportContent,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[ReportVersionRead]:
    repository = ReportRepository(db)
    report = _load_report(report_id, db)
    _ensure_report_access(report, current_user)
    version = repository.create_version(
        report_id=report.id,
        content=payload.model_dump(mode="json"),
        change_note="manual version",
    )
    return ApiResponse(data=_version_read(version))


@router.get("/{report_id}/versions", response_model=ApiResponse[list[ReportVersionRead]])
async def list_versions(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[list[ReportVersionRead]]:
    repository = ReportRepository(db)
    report = _load_report(report_id, db)
    _ensure_report_access(report, current_user)
    versions = repository.list_versions(report.id)
    return ApiResponse(data=[_version_read(version) for version in versions])


@router.post("/{report_id}/export", response_model=ApiResponse[ExportResult])
async def export_report(
    report_id: int,
    payload: dict[str, object],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[ExportResult]:
    repository = ReportRepository(db)
    report = _load_report(report_id, db)
    _ensure_report_access(report, current_user)
    export_type = str(payload.get("export_type", "json")).lower()
    template_path = _template_path_for_export(report, payload, db, current_user)
    template_suffix = Path(template_path).suffix.lower() if template_path else ""
    report_content = _report_content(report)

    if export_type in {"docx", "word"} and template_path and template_suffix == ".docx":
        result = await template_word_export_service.export_with_template(
            report_content,
            export_type,
            template_path,
        )
    elif export_type in {"xlsx", "excel"} and template_path and template_suffix == ".xlsx":
        result = await template_excel_export_service.export_with_template(
            report_content,
            export_type,
            template_path,
        )
    else:
        export_service = _get_export_service(export_type)
        result = await export_service.export(report_content, export_type)

    repository.create_export_record(
        report_id=report.id,
        export_type=result.export_type,
        file_path=result.file_path,
        status=result.status,
    )
    return ApiResponse(data=result)


def _get_export_service(export_type: str) -> ExportService:
    if export_type in {"docx", "word"}:
        return word_export_service
    if export_type in {"xlsx", "excel"}:
        return excel_export_service
    if export_type == "pdf":
        return pdf_export_service
    return mock_export_service


def _template_path_for_export(
    report: Report,
    payload: dict[str, object],
    db: Session,
    current_user: User | None,
) -> str | None:
    explicit_template_path = payload.get("template_path")
    if isinstance(explicit_template_path, str) and explicit_template_path:
        return explicit_template_path

    template_id = _payload_template_id(payload) or report.template_id
    template_context = load_template_context(
        db,
        template_id,
        current_user.id if current_user else None,
    )
    return template_context.file_path if template_context else None


def _payload_template_id(payload: dict[str, object]) -> int | None:
    raw_template_id = payload.get("template_id")
    if isinstance(raw_template_id, int):
        return raw_template_id
    if isinstance(raw_template_id, str) and raw_template_id.isdigit():
        return int(raw_template_id)
    return None


def _build_initial_report_content(payload: ReportCreate) -> ReportContent:
    content = payload.source_data.get("content")
    if isinstance(content, dict):
        content_data = {
            **content,
            "report_type": payload.report_type,
            "title": payload.title,
            "date": payload.report_date,
        }
        return ReportContent.model_validate(content_data)

    summary = payload.source_data.get("summary")
    return ReportContent(
        report_type=payload.report_type,
        title=payload.title,
        date=payload.report_date,
        summary=str(summary) if summary else "暂无报表摘要。",
    )


def _load_report(report_id: int, db: Session) -> Report:
    repository = ReportRepository(db)
    report = repository.get(report_id)
    if report is None:
        raise ResourceNotFoundError()
    return report


def _ensure_report_access(report: Report, user: User | None) -> None:
    if user is not None and report.user_id not in {None, user.id}:
        raise PermissionDeniedError()


def _report_content(report: Report, render_template: bool = True) -> ReportContent:
    content = dict(report.content or {})
    content.setdefault("report_type", report.report_type)
    content.setdefault("title", report.title)
    content.setdefault("date", report.report_date)
    content.setdefault("summary", "")
    report_content = ReportContent.model_validate(content)
    if not render_template:
        return report_content
    return _content_with_rendered_template(report_content, report)


def _content_with_rendered_template(content: ReportContent, report: Report) -> ReportContent:
    if report.template is None:
        return content
    file_path = template_file_path(report.template)
    template_text = template_render_text(report.template.field_config or {}, file_path)
    if not template_text:
        return content
    return _content_with_rendered_text(content, template_text)


def _content_with_rendered_text(content: ReportContent, template_text: str) -> ReportContent:
    custom_fields = dict(content.custom_fields)
    custom_fields["rendered_template"] = render_template_text(template_text, content)
    return content.model_copy(update={"custom_fields": custom_fields})


def _report_read(report: Report) -> ReportRead:
    return ReportRead(
        id=report.id,
        user_id=report.user_id,
        template_id=report.template_id,
        report_type=report.report_type,
        title=report.title,
        report_date=report.report_date,
        status=report.status,
        content=_report_content(report),
        source_data=report.source_data or {},
    )


def _report_summary(report: Report) -> ReportSummary:
    content = _report_content(report, render_template=False)
    return ReportSummary(
        id=report.id,
        report_type=report.report_type,
        title=report.title,
        report_date=report.report_date,
        status=report.status,
        task_count=len(content.completed_tasks) + len(content.in_progress_tasks),
    )


def _version_read(version: ReportVersion) -> ReportVersionRead:
    content_data = dict(version.content or {})
    return ReportVersionRead(
        id=version.id,
        report_id=version.report_id,
        version_number=version.version_number,
        content=ReportContent.model_validate(content_data),
        change_note=version.change_note,
        created_at=version.created_at,
    )

from __future__ import annotations

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
from app.services.export.template_word import TemplateWordExportService
from app.services.export.word import WordExportService

router = APIRouter()
mock_export_service = MockExportService()
word_export_service = WordExportService()
template_word_export_service = TemplateWordExportService()
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
        report.content = payload.content.model_dump(mode="json")
        report.report_type = payload.content.report_type
        report.title = payload.title or payload.content.title
        report.report_date = payload.content.date

    report = repository.save(report)
    if payload.content is not None:
        repository.create_version(
            report_id=report.id,
            content=payload.content.model_dump(mode="json"),
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
    template_path = payload.get("template_path")
    report_content = _report_content(report)

    if export_type in {"docx", "word"} and isinstance(template_path, str) and template_path:
        result = await template_word_export_service.export_with_template(
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


def _report_content(report: Report) -> ReportContent:
    content = dict(report.content or {})
    content.setdefault("report_type", report.report_type)
    content.setdefault("title", report.title)
    content.setdefault("date", report.report_date)
    content.setdefault("summary", "")
    return ReportContent.model_validate(content)


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
    content = _report_content(report)
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

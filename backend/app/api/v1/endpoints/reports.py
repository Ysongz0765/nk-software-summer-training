from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.models.report import Report
from app.repositories.report import ReportRepository
from app.schemas.common import ApiResponse
from app.schemas.report import (
    ExportResult,
    ReportContent,
    ReportCreate,
    ReportSummary,
    ReportUpdate,
)
from app.services.export.mock import MockExportService
from app.services.export.template_word import TemplateWordExportService
from app.services.export.word import WordExportService

router = APIRouter()
mock_export_service = MockExportService()
word_export_service = WordExportService()
template_word_export_service = TemplateWordExportService()


@router.post("", response_model=ApiResponse[dict[str, object]])
async def create_report(
    payload: ReportCreate,
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[dict[str, object]]:
    repository = ReportRepository(db)
    content = _build_initial_report_content(payload)
    report = repository.create(
        Report(
            template_id=payload.template_id,
            report_type=payload.report_type,
            title=payload.title,
            report_date=payload.report_date,
            status="draft",
            content=content.model_dump(mode="json"),
            source_data=payload.source_data,
        )
    )
    return ApiResponse(
        data={
            "id": report.id,
            "user_id": report.user_id,
            "template_id": report.template_id,
            "report_type": report.report_type,
            "title": report.title,
            "report_date": report.report_date,
            "status": report.status,
            "content": report.content,
            "source_data": report.source_data,
        }
    )


@router.get("", response_model=ApiResponse[list[ReportSummary]])
async def list_reports() -> ApiResponse[list[ReportSummary]]:
    return ApiResponse(
        data=[
            ReportSummary(
                report_type="daily",
                title="Mock report",
                report_date=date(2026, 7, 16),
                status="draft",
                task_count=3,
            )
        ]
    )


@router.get("/{report_id}", response_model=ApiResponse[dict[str, object]])
async def get_report(report_id: int) -> ApiResponse[dict[str, object]]:
    if report_id <= 0:
        raise ResourceNotFoundError()
    return ApiResponse(data={"id": report_id, "title": "Mock report", "status": "draft"})


@router.put("/{report_id}", response_model=ApiResponse[dict[str, object]])
async def update_report(report_id: int, payload: ReportUpdate) -> ApiResponse[dict[str, object]]:
    return ApiResponse(
        data={
            "id": report_id,
            "title": payload.title or "Mock report",
            "status": payload.status or "draft",
            "content": payload.content.model_dump()
            if payload.content
            else {"summary": "Mock report"},
        }
    )


@router.post("/{report_id}/versions", response_model=ApiResponse[dict[str, object]])
async def create_version(report_id: int, payload: ReportContent) -> ApiResponse[dict[str, object]]:
    return ApiResponse(
        data={
            "report_id": report_id,
            "version_number": 1,
            "content": payload.model_dump(),
        }
    )


@router.get("/{report_id}/versions", response_model=ApiResponse[list[dict[str, object]]])
async def list_versions(report_id: int) -> ApiResponse[list[dict[str, object]]]:
    return ApiResponse(
        data=[
            {
                "report_id": report_id,
                "version_number": 1,
                "change_note": "initial mock",
            }
        ]
    )


@router.post("/{report_id}/export", response_model=ApiResponse[ExportResult])
async def export_report(
    report_id: int,
    payload: dict[str, object],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ExportResult]:
    export_type = str(payload.get("export_type", "json")).lower()
    template_path = payload.get("template_path")
    report = _load_report_content(report_id, db)

    if export_type in {"docx", "word"} and isinstance(template_path, str) and template_path:
        result = await template_word_export_service.export_with_template(
            report,
            export_type,
            template_path,
        )
    else:
        export_service = (
            word_export_service if export_type in {"docx", "word"} else mock_export_service
        )
        result = await export_service.export(report, export_type)
    return ApiResponse(data=result)


def _build_initial_report_content(payload: ReportCreate) -> ReportContent:
    content = payload.source_data.get("content")
    if isinstance(content, dict):
        content_data = {
            "report_type": payload.report_type,
            "title": payload.title,
            "date": payload.report_date,
            **content,
        }
        return ReportContent.model_validate(content_data)

    summary = payload.source_data.get("summary")
    return ReportContent(
        report_type=payload.report_type,
        title=payload.title,
        date=payload.report_date,
        summary=str(summary) if summary else "暂无报表摘要。",
    )


def _load_report_content(report_id: int, db: Session) -> ReportContent:
    repository = ReportRepository(db)
    report = repository.get(report_id)
    if report is None:
        raise ResourceNotFoundError()

    content = dict(report.content or {})
    content.setdefault("report_type", report.report_type)
    content.setdefault("title", report.title)
    content.setdefault("date", report.report_date)
    content.setdefault("summary", "")
    return ReportContent.model_validate(content)

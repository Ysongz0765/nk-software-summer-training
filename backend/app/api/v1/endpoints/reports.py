from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from app.core.exceptions import ResourceNotFoundError
from app.schemas.common import ApiResponse
from app.schemas.report import (
    ExportResult,
    ReportContent,
    ReportCreate,
    ReportSummary,
    ReportUpdate,
)
from app.services.export.mock import MockExportService

router = APIRouter()
export_service = MockExportService()


@router.post("", response_model=ApiResponse[dict[str, object]])
async def create_report(payload: ReportCreate) -> ApiResponse[dict[str, object]]:
    return ApiResponse(
        data={
            "id": 1,
            "user_id": None,
            "template_id": payload.template_id,
            "report_type": payload.report_type,
            "title": payload.title,
            "report_date": payload.report_date,
            "status": "draft",
            "content": {"summary": "Mock report"},
            "source_data": payload.source_data,
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
async def export_report(report_id: int, payload: dict[str, object]) -> ApiResponse[ExportResult]:
    report = ReportContent(
        report_type="daily",
        title="Mock report",
        date=date(2026, 7, 16),
        summary="Mock report",
    )
    result = await export_service.export(report, str(payload.get("export_type", "json")))
    return ApiResponse(data=result)

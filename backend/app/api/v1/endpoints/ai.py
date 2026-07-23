from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.schemas.common import ApiResponse
from app.schemas.report import (
    MissingInformationResult,
    ReportContent,
    ReportGenerationRequest,
    TaskExtractionInput,
    TaskItem,
)
from app.services.ai.base import AIReportService
from app.services.ai.factory import get_ai_report_service

router = APIRouter()


@router.post("/extract-tasks", response_model=ApiResponse[list[TaskItem]])
async def extract_tasks(
    payload: TaskExtractionInput,
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
) -> ApiResponse[list[TaskItem]]:
    tasks = await ai_service.extract_tasks(payload)
    return ApiResponse(data=tasks)


@router.post("/check-missing", response_model=ApiResponse[MissingInformationResult])
async def check_missing(
    payload: list[TaskItem],
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
) -> ApiResponse[MissingInformationResult]:
    result = await ai_service.check_missing_information(payload)
    return ApiResponse(data=result)


@router.post("/generate-report", response_model=ApiResponse[ReportContent])
async def generate_report(
    payload: ReportGenerationRequest,
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
) -> ApiResponse[ReportContent]:
    report = await ai_service.generate_report(payload)
    return ApiResponse(data=report)

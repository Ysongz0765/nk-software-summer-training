from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.report import (
    MissingInformationResult,
    ReportContent,
    ReportGenerationRequest,
    TaskExtractionInput,
    TaskItem,
)
from app.services.ai.mock import MockAIReportService

router = APIRouter()
ai_service = MockAIReportService()


@router.post("/extract-tasks", response_model=ApiResponse[list[TaskItem]])
async def extract_tasks(payload: TaskExtractionInput) -> ApiResponse[list[TaskItem]]:
    tasks = await ai_service.extract_tasks(payload)
    return ApiResponse(data=tasks)


@router.post("/check-missing", response_model=ApiResponse[MissingInformationResult])
async def check_missing(payload: list[TaskItem]) -> ApiResponse[MissingInformationResult]:
    result = await ai_service.check_missing_information(payload)
    return ApiResponse(data=result)


@router.post("/generate-report", response_model=ApiResponse[ReportContent])
async def generate_report(payload: ReportGenerationRequest) -> ApiResponse[ReportContent]:
    report = await ai_service.generate_report(payload)
    return ApiResponse(data=report)

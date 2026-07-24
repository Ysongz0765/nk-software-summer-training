from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.report import (
    MissingInformationRequest,
    MissingInformationResult,
    ReportContent,
    ReportGenerationRequest,
    TaskExtractionInput,
    TaskItem,
)
from app.services.ai.base import AIReportService
from app.services.ai.factory import get_ai_report_service
from app.services.template.context import TemplateContext, load_template_context

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
    payload: list[TaskItem] | MissingInformationRequest,
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[MissingInformationResult]:
    request = _missing_information_request(payload)
    template_context = load_template_context(
        db,
        request.template_id,
        current_user.id if current_user else None,
    )
    source_data = _source_data_with_template(request.source_data, template_context)
    template_fields = _merge_template_fields(
        request.template_fields,
        template_context.fields if template_context else [],
    )
    result = await ai_service.check_missing_information(
        request.tasks,
        template_fields,
        source_data,
    )
    return ApiResponse(data=result)


@router.post("/generate-report", response_model=ApiResponse[ReportContent])
async def generate_report(
    payload: ReportGenerationRequest,
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[ReportContent]:
    template_context = load_template_context(
        db,
        payload.template_id,
        current_user.id if current_user else None,
    )
    request = payload.model_copy(
        update={
            "template_fields": _merge_template_fields(
                payload.template_fields,
                template_context.fields if template_context else [],
            ),
            "source_data": _source_data_with_template(payload.source_data, template_context),
        },
    )
    report = await ai_service.generate_report(request)
    return ApiResponse(data=report)


def _missing_information_request(
    payload: list[TaskItem] | MissingInformationRequest,
) -> MissingInformationRequest:
    if isinstance(payload, MissingInformationRequest):
        return payload
    return MissingInformationRequest(tasks=payload)


def _merge_template_fields(*field_lists: list[str]) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for field_list in field_lists:
        for raw_field in field_list:
            field = raw_field.strip()
            if not field or field in seen:
                continue
            fields.append(field)
            seen.add(field)
    return fields


def _source_data_with_template(
    source_data: dict[str, object],
    template_context: TemplateContext | None,
) -> dict[str, object]:
    data = dict(source_data)
    if template_context is not None:
        data["template"] = template_context.model_payload()
    return data

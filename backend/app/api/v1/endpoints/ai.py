from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.schemas.common import ApiResponse
from app.schemas.report import (
    GitHubProgressAnalysisRequest,
    GitHubProgressAnalysisResult,
    MissingInformationRequest,
    MissingInformationResult,
    ReportContent,
    ReportGenerationRequest,
    TaskExtractionInput,
    TaskItem,
)
from app.services.ai.base import AIReportService
from app.services.ai.factory import get_ai_report_service
from app.services.github_progress import GitHubProgressService, format_github_progress_snapshot
from app.services.project_context import (
    build_ai_project_context,
    ensure_project_access,
    project_tasks_to_task_items,
    selected_project_tasks,
)
from app.services.template.context import TemplateContext, load_template_context

router = APIRouter()


@router.post("/extract-tasks", response_model=ApiResponse[list[TaskItem]])
async def extract_tasks(
    payload: TaskExtractionInput,
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
) -> ApiResponse[list[TaskItem]]:
    tasks = await ai_service.extract_tasks(payload)
    return ApiResponse(data=tasks)


@router.post("/analyze-github-progress", response_model=ApiResponse[GitHubProgressAnalysisResult])
async def analyze_github_progress(
    payload: GitHubProgressAnalysisRequest,
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
) -> ApiResponse[GitHubProgressAnalysisResult]:
    settings = get_settings()
    github_service = GitHubProgressService(
        api_token=settings.github_api_token,
        base_url=settings.github_api_base_url,
        timeout_seconds=settings.github_timeout_seconds,
    )
    snapshot = await github_service.fetch_progress_snapshot(
        payload.repo_url,
        max_items=payload.max_items,
    )
    source_text = format_github_progress_snapshot(snapshot)
    repository = snapshot.get("repository") if isinstance(snapshot.get("repository"), dict) else {}
    tasks = await ai_service.extract_tasks(
        TaskExtractionInput(
            source_text=source_text,
            report_type=payload.report_type,
            context={
                "source": "github_api",
                "repo_url": payload.repo_url,
                "repository": repository,
            },
        )
    )
    tasks = [task.model_copy(update={"source": "github"}) for task in tasks]
    return ApiResponse(
        data=GitHubProgressAnalysisResult(
            repo_url=payload.repo_url,
            repository=repository,
            source_text=source_text,
            tasks=tasks,
        )
    )


@router.post("/check-missing", response_model=ApiResponse[MissingInformationResult])
async def check_missing(
    payload: list[TaskItem] | MissingInformationRequest,
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)],
) -> ApiResponse[MissingInformationResult]:
    request = _missing_information_request(payload)
    if request.project_id is not None:
        ensure_project_access(db, request.project_id, current_user)
    template_context = load_template_context(
        db,
        request.template_id,
        current_user.id if current_user else None,
        project_id=request.project_id,
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
    project = None
    project_context: dict[str, object] | None = None
    project_tasks: list[TaskItem] = []
    if payload.project_id is not None:
        project = ensure_project_access(db, payload.project_id, current_user)
        period_start = payload.start_date or payload.report_date
        period_end = payload.end_date or payload.report_date
        project_context = build_ai_project_context(
            db,
            project,
            start_date=period_start,
            end_date=period_end,
            file_ids=payload.file_ids,
            task_ids=payload.task_ids,
            user_notes=payload.user_notes,
        )
        loaded_tasks = selected_project_tasks(db, project.id, payload.task_ids)
        if not loaded_tasks and not payload.tasks:
            loaded_tasks = ProjectRepository(db).list_tasks(project.id)[:10]
        project_tasks = project_tasks_to_task_items(loaded_tasks)

    template_context = load_template_context(
        db,
        payload.template_id,
        current_user.id if current_user else None,
        project_id=payload.project_id,
    )
    source_data = _source_data_with_template(payload.source_data, template_context)
    if project_context is not None:
        source_data["project_context"] = project_context
        source_data["project_id"] = payload.project_id
    request = payload.model_copy(
        update={
            "title": payload.title or _default_project_report_title(project, payload.report_type),
            "tasks": _merge_tasks(payload.tasks, project_tasks),
            "template_fields": _merge_template_fields(
                payload.template_fields,
                template_context.fields if template_context else [],
            ),
            "source_data": source_data,
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


def _merge_tasks(primary: list[TaskItem], extra: list[TaskItem]) -> list[TaskItem]:
    merged: list[TaskItem] = []
    seen: set[str] = set()
    for task in [*primary, *extra]:
        if task.id in seen:
            continue
        merged.append(task)
        seen.add(task.id)
    return merged


def _default_project_report_title(project: object, report_type: str) -> str:
    project_name = getattr(project, "name", "")
    if isinstance(project_name, str) and project_name:
        return f"{project_name}{'日报' if report_type == 'daily' else '周报'}"
    return ""

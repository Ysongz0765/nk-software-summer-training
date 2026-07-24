from __future__ import annotations

import hashlib
import re

from app.schemas.report import (
    MissingInformationResult,
    ReportContent,
    ReportGenerationRequest,
    TaskExtractionInput,
    TaskItem,
)
from app.services.ai.base import AIReportService
from app.services.template.context import (
    STANDARD_TEMPLATE_FIELDS,
    custom_field_name,
    get_source_value,
)
from app.services.template.render import render_template_text

DEFAULT_TASK_LINES = (
    "完成数据库表设计",
    "联调后端健康检查接口",
    "整理项目需求文档",
)
MAX_MOCK_TASKS = 5


class MockAIReportService(AIReportService):
    async def extract_tasks(self, input_data: TaskExtractionInput) -> list[TaskItem]:
        candidates = _extract_task_candidates(input_data.source_text) or list(DEFAULT_TASK_LINES)
        return [
            _build_mock_task(candidate, index)
            for index, candidate in enumerate(candidates[:MAX_MOCK_TASKS], start=1)
        ]

    async def check_missing_information(
        self,
        tasks: list[TaskItem],
        template_fields: list[str] | None = None,
        source_data: dict[str, object] | None = None,
    ) -> MissingInformationResult:
        missing: list[str] = []
        questions: list[str] = []
        source = source_data or {}

        if not tasks:
            missing.append("tasks")
            questions.append("请补充本次日报或周报包含的任务。")
        if tasks and not all(task.user_confirmed for task in tasks):
            missing.append("task_confirmation")
            questions.append("请确认未确认任务的标题、状态和进度是否准确。")
        if any(not task.description for task in tasks):
            missing.append("task_descriptions")
            questions.append("请补充任务背景、交付物或关键处理过程。")
        if any(task.confidence < 0.75 for task in tasks):
            missing.append("low_confidence_tasks")
            questions.append("请确认低置信度任务的标题、状态和进度。")
        if tasks and all(task.status == "completed" for task in tasks):
            missing.append("next_plan")
            questions.append("请补充下一阶段计划。")

        for field in template_fields or []:
            _append_template_missing_field(field, source, missing, questions)

        return MissingInformationResult(
            missing_fields=missing,
            questions=questions,
            confidence=max(0.5, 0.95 - len(missing) * 0.08),
        )

    async def generate_report(self, request: ReportGenerationRequest) -> ReportContent:
        completed = [task for task in request.tasks if task.status == "completed"]
        active = [task for task in request.tasks if task.status != "completed"]
        missing_result = await self.check_missing_information(
            request.tasks,
            request.template_fields,
            request.source_data,
        )
        problems = _string_list_from_source(request.source_data, "problems")
        solutions = _string_list_from_source(request.source_data, "solutions")
        next_plan = _string_list_from_source(request.source_data, "next_plan")

        if not problems:
            problems = [
                "部分任务信息仍需人工确认。"
                if missing_result.missing_fields
                else "暂无阻塞问题。"
            ]
        if not solutions:
            solutions = [
                "根据补充信息更新报表内容。"
                if missing_result.missing_fields
                else "保持当前推进节奏。"
            ]
        if not next_plan:
            next_plan = [f"继续推进：{task.title}" for task in active[:3]] or [
                "沉淀本期成果并准备下一期计划。"
            ]

        custom_fields = _build_template_custom_fields(request)
        report = ReportContent(
            report_type=request.report_type,
            title=request.title,
            date=request.report_date,
            summary=(
                f"本期共识别 {len(request.tasks)} 项任务，"
                f"已完成 {len(completed)} 项，推进中 {len(active)} 项。"
            ),
            completed_tasks=completed,
            in_progress_tasks=active,
            problems=problems,
            solutions=solutions,
            next_plan=next_plan,
            custom_fields={
                **custom_fields,
                "template_id": request.template_id,
                "style": request.style,
                "generated_by": "MockAIReportService",
            },
            missing_fields=missing_result.missing_fields,
            style=request.style,
        )
        rendered_template = _render_template_body(request, report)
        if rendered_template:
            report.custom_fields["rendered_template"] = rendered_template
        return report


def _extract_task_candidates(source_text: str) -> list[str]:
    raw_parts: list[str] = []
    for line in source_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        raw_parts.extend(re.split(r"[。；;!?！？]+", line))

    candidates: list[str] = []
    seen: set[str] = set()
    for raw_part in raw_parts:
        candidate = re.sub(r"^\s*(?:[-*]|\d+[.)、]|[（(]?\d+[）)])\s*", "", raw_part).strip()
        candidate = re.sub(r"\s+", " ", candidate)
        if not candidate or candidate in seen:
            continue
        candidates.append(candidate)
        seen.add(candidate)
    return candidates


def _build_mock_task(candidate: str, index: int) -> TaskItem:
    status, progress = _infer_status(candidate)
    title = _build_title(candidate, index)
    task_id = hashlib.sha1(f"{index}:{candidate}".encode()).hexdigest()[:10]
    return TaskItem(
        id=f"mock-task-{task_id}",
        title=title,
        description=f"从输入内容识别：{candidate}",
        status=status,
        progress=progress,
        confidence=_confidence_for_status(status),
        source="mock",
        user_confirmed=status == "completed",
    )


def _infer_status(text: str) -> tuple[str, int]:
    lowered = text.lower()
    if any(keyword in text for keyword in ("待", "计划", "准备", "未完成")) or "todo" in lowered:
        return "pending", 20
    if (
        text.startswith("完成")
        or any(keyword in text for keyword in ("已完成", "已提交", "上线", "修复"))
        or any(keyword in lowered for keyword in ("done", "finished", "fixed"))
    ):
        return "completed", 100
    if any(keyword in text for keyword in ("进行中", "正在", "联调", "开发中", "处理中")):
        return "in_progress", 70
    return "in_progress", 50


def _build_title(candidate: str, index: int) -> str:
    title = candidate.strip()
    if len(title) > 36:
        title = f"{title[:33]}..."
    return title or f"待确认任务 {index}"


def _confidence_for_status(status: str) -> float:
    return {
        "completed": 0.94,
        "in_progress": 0.88,
        "pending": 0.8,
    }.get(status, 0.75)


def _string_list_from_source(source_data: dict[str, object], key: str) -> list[str]:
    value = get_source_value(source_data, key)
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _append_template_missing_field(
    field: str,
    source_data: dict[str, object],
    missing: list[str],
    questions: list[str],
) -> None:
    normalized = field.strip()
    if not normalized:
        return
    if normalized in {"title", "date", "report_type", "summary"}:
        return
    if normalized in {"completed_tasks", "in_progress_tasks"}:
        return
    if normalized in missing:
        return
    if get_source_value(source_data, normalized) is not None:
        return

    custom_name = custom_field_name(normalized)
    if custom_name is not None:
        missing.append(normalized)
        questions.append(f"Please provide a value for template field '{custom_name}'.")
        return

    if normalized in {"problems", "solutions", "next_plan"}:
        missing.append(normalized)
        questions.append(f"Please provide content for template field '{normalized}'.")


def _build_template_custom_fields(request: ReportGenerationRequest) -> dict[str, object]:
    custom_fields: dict[str, object] = {}
    for field in request.template_fields:
        custom_name = custom_field_name(field)
        if custom_name is None:
            continue
        value = get_source_value(request.source_data, field)
        if value is None:
            value = get_source_value(request.source_data, custom_name)
        custom_fields[custom_name] = value if value is not None else _fallback_custom_field_value(
            custom_name,
        )

    template_context = request.source_data.get("template")
    if isinstance(template_context, dict):
        custom_fields.setdefault("template_name", str(template_context.get("name", "")))
        fields = template_context.get("fields")
        if isinstance(fields, list):
            custom_fields.setdefault(
                "template_fields",
                ", ".join(field for field in fields if isinstance(field, str)),
            )
    return custom_fields


def _fallback_custom_field_value(field: str) -> str:
    if field in STANDARD_TEMPLATE_FIELDS:
        return ""
    return "TBD"


def _render_template_body(
    request: ReportGenerationRequest,
    report: ReportContent,
) -> str | None:
    template_context = request.source_data.get("template")
    if not isinstance(template_context, dict):
        return None
    render_text = template_context.get("render_text")
    if not isinstance(render_text, str) or not render_text.strip():
        return None
    return render_template_text(render_text, report)

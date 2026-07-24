from __future__ import annotations

import re

from app.schemas.report import ReportContent, TaskItem

PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([^{}\r\n]+?)\s*\}\}")

FIELD_ALIASES = {
    "报告标题": "title",
    "报表标题": "title",
    "标题": "title",
    "报告日期": "date",
    "报表日期": "date",
    "日期": "date",
    "类型": "report_type",
    "报表类型": "report_type",
    "工作总结": "summary",
    "今日总结": "summary",
    "本日总结": "summary",
    "本周总结": "summary",
    "总结": "summary",
    "摘要": "summary",
    "任务完成情况": "completed_tasks",
    "完成情况": "completed_tasks",
    "完成任务": "completed_tasks",
    "已完成任务": "completed_tasks",
    "今日完成": "completed_tasks",
    "本日完成": "completed_tasks",
    "本周完成": "completed_tasks",
    "进行中任务": "in_progress_tasks",
    "推进中任务": "in_progress_tasks",
    "未完成任务": "in_progress_tasks",
    "待完成任务": "in_progress_tasks",
    "问题与风险": "problems",
    "问题风险": "problems",
    "存在问题": "problems",
    "风险": "problems",
    "问题": "problems",
    "解决方案": "solutions",
    "解决措施": "solutions",
    "处理措施": "solutions",
    "应对措施": "solutions",
    "明日计划": "next_plan",
    "下周计划": "next_plan",
    "下一步计划": "next_plan",
    "下步计划": "next_plan",
    "后续计划": "next_plan",
}


def canonical_field_name(field: str) -> str:
    normalized = _normalize_placeholder_name(field)
    if normalized in FIELD_ALIASES:
        return FIELD_ALIASES[normalized]
    lowered = normalized.lower()
    return FIELD_ALIASES.get(lowered, lowered)


def extract_placeholders(template_text: str) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for raw_field in PLACEHOLDER_PATTERN.findall(template_text):
        field = canonical_field_name(raw_field)
        if not field or field in seen:
            continue
        fields.append(field)
        seen.add(field)
    return fields


def extract_raw_placeholders(template_text: str) -> list[str]:
    fields: list[str] = []
    seen: set[str] = set()
    for raw_field in PLACEHOLDER_PATTERN.findall(template_text):
        field = _normalize_placeholder_name(raw_field)
        if not field or field in seen:
            continue
        fields.append(field)
        seen.add(field)
    return fields


def render_template_text(template_text: str, report: ReportContent) -> str:
    replacements = build_replacements(report)
    return PLACEHOLDER_PATTERN.sub(
        lambda match: replacements.get(
            _normalize_placeholder_name(match.group(1)),
            replacements.get(canonical_field_name(match.group(1)), match.group(0)),
        ),
        template_text,
    )


def build_replacements(report: ReportContent) -> dict[str, str]:
    replacements = {
        "report_type": _report_type_label(report.report_type),
        "title": report.title,
        "date": report.date.isoformat(),
        "summary": report.summary,
        "completed_tasks": _format_tasks(report.completed_tasks),
        "in_progress_tasks": _format_tasks(report.in_progress_tasks),
        "problems": _format_list(report.problems),
        "solutions": _format_list(report.solutions),
        "next_plan": _format_list(report.next_plan),
        "style": report.style,
    }
    for alias, canonical in FIELD_ALIASES.items():
        if canonical in replacements:
            replacements[alias] = replacements[canonical]
    for key, value in report.custom_fields.items():
        rendered_value = format_custom_value(value)
        replacements.setdefault(key, rendered_value)
        replacements[f"custom_fields.{key}"] = rendered_value
    return replacements


def format_custom_value(value: object) -> str:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {item}" for key, item in value.items())
    return str(value)


def _format_tasks(tasks: list[TaskItem]) -> str:
    if not tasks:
        return "暂无"
    return "\n".join(
        f"{index}. {task.title}"
        f"{f'：{task.description}' if task.description else ''}"
        f"（进度 {task.progress}%）"
        for index, task in enumerate(tasks, start=1)
    )


def _format_list(items: list[str]) -> str:
    if not items:
        return "暂无"
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def _report_type_label(report_type: str) -> str:
    labels = {"daily": "日报", "weekly": "周报"}
    return labels.get(report_type, report_type)


def _normalize_placeholder_name(field: str) -> str:
    return field.strip().strip(":：")

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile

from app.core.config import get_settings
from app.schemas.report import ExportResult, ReportContent, TaskItem
from app.services.export.base import ExportService

PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\}\}")
WORD_NAMESPACE = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"

ElementTree.register_namespace("w", WORD_NAMESPACE)


class TemplateWordExportService(ExportService):
    async def export(self, report: ReportContent, export_type: str) -> ExportResult:
        return await self.export_with_template(report, export_type, None)

    async def export_with_template(
        self,
        report: ReportContent,
        export_type: str,
        template_path: str | None,
    ) -> ExportResult:
        if export_type.lower() not in {"docx", "word"}:
            msg = f"Unsupported Word export type: {export_type}"
            raise ValueError(msg)
        if not template_path:
            msg = "template_path is required for template Word export."
            raise ValueError(msg)

        source_template = Path(template_path)
        if source_template.suffix.lower() != ".docx":
            msg = "Only .docx template files are supported now."
            raise ValueError(msg)
        if not source_template.exists():
            msg = f"Template file not found: {template_path}"
            raise FileNotFoundError(msg)

        settings = get_settings()
        export_dir = Path(settings.storage_root) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_title = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+", "_", report.title).strip("_")
        target_path = export_dir / f"{safe_title or 'report'}-template-{uuid4().hex[:8]}.docx"

        replacements = _build_replacements(report)
        _render_docx_template(source_template, target_path, replacements)

        return ExportResult(
            export_type="docx",
            file_path=str(target_path),
            status="success",
            download_url=f"/storage/exports/{target_path.name}",
        )


def _render_docx_template(
    source_template: Path,
    target_path: Path,
    replacements: dict[str, str],
) -> None:
    with ZipFile(source_template) as source_docx:
        with ZipFile(target_path, "w", ZIP_DEFLATED) as target_docx:
            for item in source_docx.infolist():
                content = source_docx.read(item.filename)
                if _is_word_text_xml(item.filename):
                    content = _replace_placeholders_in_xml(content, replacements)
                target_docx.writestr(item, content)


def _is_word_text_xml(file_name: str) -> bool:
    return file_name == "word/document.xml" or file_name.startswith(
        ("word/header", "word/footer")
    )


def _replace_placeholders_in_xml(xml_content: bytes, replacements: dict[str, str]) -> bytes:
    root = ElementTree.fromstring(xml_content)
    changed = False

    for paragraph in root.iter(f"{{{WORD_NAMESPACE}}}p"):
        text_nodes = list(paragraph.iter(f"{{{WORD_NAMESPACE}}}t"))
        if not text_nodes:
            continue

        original_text = "".join(text_node.text or "" for text_node in text_nodes)
        rendered_text = PLACEHOLDER_PATTERN.sub(
            lambda match: replacements.get(match.group(1), match.group(0)),
            original_text,
        )
        if rendered_text == original_text:
            continue

        text_nodes[0].text = rendered_text
        text_nodes[0].set(f"{{{XML_NAMESPACE}}}space", "preserve")
        for text_node in text_nodes[1:]:
            text_node.text = ""
        changed = True

    if not changed:
        return xml_content
    return ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)


def _build_replacements(report: ReportContent) -> dict[str, str]:
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
    for key, value in report.custom_fields.items():
        replacements[f"custom_fields.{key}"] = str(value)
    return replacements


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

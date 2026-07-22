from __future__ import annotations

import html
import re
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from app.core.config import get_settings
from app.schemas.report import ExportResult, ReportContent, TaskItem
from app.services.export.base import ExportService


class WordExportService(ExportService):
    async def export(self, report: ReportContent, export_type: str) -> ExportResult:
        if export_type.lower() not in {"docx", "word"}:
            msg = f"Unsupported Word export type: {export_type}"
            raise ValueError(msg)

        settings = get_settings()
        export_dir = Path(settings.storage_root) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_title = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+", "_", report.title).strip("_")
        file_name = f"{safe_title or 'report'}-{uuid4().hex[:8]}.docx"
        file_path = export_dir / file_name

        document_xml = _build_document_xml(report)
        _write_docx(file_path, document_xml)

        return ExportResult(
            export_type="docx",
            file_path=str(file_path),
            status="success",
            download_url=f"/storage/exports/{file_path.name}",
        )


def _build_document_xml(report: ReportContent) -> str:
    paragraphs: list[str] = []
    paragraphs.append(_paragraph(report.title, style="Title"))
    paragraphs.append(_paragraph(f"报表类型：{_report_type_label(report.report_type)}"))
    paragraphs.append(_paragraph(f"日期：{report.date.isoformat()}"))
    paragraphs.append(_paragraph(""))
    paragraphs.append(_heading("一、工作总结"))
    paragraphs.append(_paragraph(report.summary))
    paragraphs.append(_heading("二、已完成任务"))
    paragraphs.extend(_task_paragraphs(report.completed_tasks))
    paragraphs.append(_heading("三、进行中任务"))
    paragraphs.extend(_task_paragraphs(report.in_progress_tasks))
    paragraphs.append(_heading("四、问题与风险"))
    paragraphs.extend(_list_paragraphs(report.problems))
    paragraphs.append(_heading("五、解决方案"))
    paragraphs.extend(_list_paragraphs(report.solutions))
    paragraphs.append(_heading("六、下一步计划"))
    paragraphs.extend(_list_paragraphs(report.next_plan))

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {''.join(paragraphs)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"
        w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""


def _write_docx(file_path: Path, document_xml: str) -> None:
    with ZipFile(file_path, "w", ZIP_DEFLATED) as docx:
        docx.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels"
    ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
""",
        )
        docx.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>
""",
        )
        docx.writestr(
            "word/_rels/document.xml.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
""",
        )
        docx.writestr("word/document.xml", document_xml)
        docx.writestr("word/styles.xml", _styles_xml())


def _task_paragraphs(tasks: list[TaskItem]) -> list[str]:
    if not tasks:
        return [_paragraph("暂无")]
    return [
        _paragraph(
            f"{index}. {task.title}"
            f"{f'：{task.description}' if task.description else ''}"
            f"（进度 {task.progress}%）"
        )
        for index, task in enumerate(tasks, start=1)
    ]


def _list_paragraphs(items: list[str]) -> list[str]:
    if not items:
        return [_paragraph("暂无")]
    return [_paragraph(f"{index}. {item}") for index, item in enumerate(items, start=1)]


def _heading(text: str) -> str:
    return _paragraph(text, style="Heading1")


def _paragraph(text: str, style: str | None = None) -> str:
    safe_text = html.escape(text)
    style_xml = f"<w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>" if style else ""
    return f"<w:p>{style_xml}<w:r><w:t xml:space=\"preserve\">{safe_text}</w:t></w:r></w:p>"


def _report_type_label(report_type: str) -> str:
    labels = {"daily": "日报", "weekly": "周报"}
    return labels.get(report_type, report_type)


def _styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:eastAsia="Microsoft YaHei"/>
      <w:sz w:val="24"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:rPr>
      <w:b/>
      <w:rFonts w:ascii="Arial" w:eastAsia="Microsoft YaHei"/>
      <w:sz w:val="36"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:rPr>
      <w:b/>
      <w:rFonts w:ascii="Arial" w:eastAsia="Microsoft YaHei"/>
      <w:sz w:val="28"/>
    </w:rPr>
  </w:style>
</w:styles>
"""

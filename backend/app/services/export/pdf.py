from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import get_settings
from app.schemas.report import ExportResult, ReportContent, TaskItem
from app.services.export.base import ExportService

FONT_NAME = "ReportFlowCJK"
FONT_CANDIDATES = (
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/simsun.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
    Path("/usr/share/fonts/truetype/arphic/ukai.ttc"),
)
PAGE_MARGIN = 18 * mm
ACCENT_COLOR = colors.HexColor("#1F4E79")
BORDER_COLOR = colors.HexColor("#CBD5E1")
HEADER_FILL = colors.HexColor("#D9EAF7")
TEXT_COLOR = colors.HexColor("#111827")
MUTED_TEXT_COLOR = colors.HexColor("#6B7280")


class PdfExportService(ExportService):
    async def export(self, report: ReportContent, export_type: str) -> ExportResult:
        if export_type.lower() != "pdf":
            msg = f"Unsupported PDF export type: {export_type}"
            raise ValueError(msg)

        settings = get_settings()
        export_dir = Path(settings.storage_root) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_title = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+", "_", report.title).strip("_")
        file_path = export_dir / f"{safe_title or 'report'}-{uuid4().hex[:8]}.pdf"

        _write_pdf(file_path, report)

        return ExportResult(
            export_type="pdf",
            file_path=str(file_path),
            status="success",
            download_url=f"/storage/exports/{file_path.name}",
        )


def _write_pdf(file_path: Path, report: ReportContent) -> None:
    font_name = _register_chinese_font()
    styles = _build_styles(font_name)
    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        leftMargin=PAGE_MARGIN,
        rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
        title=report.title,
    )
    document.build(
        _build_story(report, styles),
        onFirstPage=lambda canvas, doc: _draw_footer(canvas, doc, font_name),
        onLaterPages=lambda canvas, doc: _draw_footer(canvas, doc, font_name),
    )


def _register_chinese_font() -> str:
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME

    for font_path in FONT_CANDIDATES:
        if not font_path.exists():
            continue
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))
        return FONT_NAME

    fallback_font = "STSong-Light"
    if fallback_font not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(fallback_font))
    return fallback_font


def _build_styles(font_name: str) -> dict[str, ParagraphStyle]:
    base_styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base_styles["Title"],
            fontName=font_name,
            fontSize=20,
            leading=28,
            textColor=TEXT_COLOR,
            spaceAfter=10,
        ),
        "meta": ParagraphStyle(
            "ReportMeta",
            parent=base_styles["Normal"],
            fontName=font_name,
            fontSize=10.5,
            leading=17,
            textColor=colors.HexColor("#374151"),
        ),
        "heading": ParagraphStyle(
            "ReportHeading",
            parent=base_styles["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=20,
            textColor=ACCENT_COLOR,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=10.5,
            leading=18,
            firstLineIndent=0,
            spaceAfter=4,
        ),
        "table_header": ParagraphStyle(
            "ReportTableHeader",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=13,
            textColor=TEXT_COLOR,
            alignment=1,
        ),
        "table_cell": ParagraphStyle(
            "ReportTableCell",
            parent=base_styles["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=13,
            textColor=TEXT_COLOR,
        ),
    }


def _build_story(report: ReportContent, styles: dict[str, ParagraphStyle]) -> list[object]:
    story: list[object] = [
        Paragraph(_escape(report.title), styles["title"]),
        Paragraph(f"报表类型：{_report_type_label(report.report_type)}", styles["meta"]),
        Paragraph(f"日期：{report.date.isoformat()}", styles["meta"]),
        Spacer(1, 8),
    ]

    _append_section(story, "一、工作总结", [report.summary], styles)
    _append_task_section(story, "二、已完成任务", report.completed_tasks, styles)
    _append_task_section(story, "三、进行中任务", report.in_progress_tasks, styles)
    _append_section(story, "四、问题与风险", _format_list(report.problems), styles)
    _append_section(story, "五、解决方案", _format_list(report.solutions), styles)
    _append_section(story, "六、下一步计划", _format_list(report.next_plan), styles)
    return story


def _append_section(
    story: list[object],
    title: str,
    lines: list[str],
    styles: dict[str, ParagraphStyle],
) -> None:
    story.append(Paragraph(_escape(title), styles["heading"]))
    for line in lines:
        story.append(Paragraph(_escape(line), styles["body"]))
    story.append(Spacer(1, 4))


def _append_task_section(
    story: list[object],
    title: str,
    tasks: list[TaskItem],
    styles: dict[str, ParagraphStyle],
) -> None:
    story.append(Paragraph(_escape(title), styles["heading"]))
    story.append(_build_task_table(tasks, styles))
    story.append(Spacer(1, 8))


def _build_task_table(tasks: list[TaskItem], styles: dict[str, ParagraphStyle]) -> Table:
    data: list[list[object]] = [
        [
            Paragraph("序号", styles["table_header"]),
            Paragraph("任务", styles["table_header"]),
            Paragraph("描述", styles["table_header"]),
            Paragraph("状态", styles["table_header"]),
            Paragraph("进度", styles["table_header"]),
        ]
    ]

    if not tasks:
        data.append(
            [
                "1",
                Paragraph("暂无", styles["table_cell"]),
                Paragraph("", styles["table_cell"]),
                "",
                "",
            ]
        )
    else:
        for index, task in enumerate(tasks, start=1):
            data.append(
                [
                    str(index),
                    Paragraph(_escape(task.title), styles["table_cell"]),
                    Paragraph(_escape(task.description or ""), styles["table_cell"]),
                    _status_label(task.status),
                    f"{task.progress}%",
                ]
            )

    table = Table(
        data,
        colWidths=[12 * mm, 42 * mm, 70 * mm, 24 * mm, 20 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
                ("TEXTCOLOR", (0, 0), (-1, 0), TEXT_COLOR),
                ("FONTNAME", (0, 0), (-1, -1), styles["table_cell"].fontName),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (3, 1), (4, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _format_list(items: list[str]) -> list[str]:
    if not items:
        return ["暂无"]
    return [f"{index}. {item}" for index, item in enumerate(items, start=1)]


def _report_type_label(report_type: str) -> str:
    labels = {"daily": "日报", "weekly": "周报"}
    return labels.get(report_type, report_type)


def _status_label(status: str) -> str:
    labels = {
        "pending": "待处理",
        "in_progress": "进行中",
        "completed": "已完成",
    }
    return labels.get(status, status)


def _draw_footer(canvas: Any, document: Any, font_name: str) -> None:
    canvas.saveState()
    canvas.setStrokeColor(BORDER_COLOR)
    canvas.line(PAGE_MARGIN, 13 * mm, A4[0] - PAGE_MARGIN, 13 * mm)
    canvas.setFont(font_name, 8)
    canvas.setFillColor(MUTED_TEXT_COLOR)
    canvas.drawRightString(A4[0] - PAGE_MARGIN, 8 * mm, f"第 {document.page} 页")
    canvas.restoreState()


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )

from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

from app.schemas.report import ReportContent, TaskItem
from app.services.export.excel import ExcelExportService
from app.services.export.pdf import PdfExportService


def test_excel_export_service_creates_xlsx(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))

    async def run() -> None:
        service = ExcelExportService()
        result = await service.export(_build_report(), "xlsx")

        assert result.export_type == "xlsx"
        assert result.file_path.endswith(".xlsx")

        workbook = load_workbook(result.file_path)
        overview = workbook["报表概览"]
        tasks = workbook["任务明细"]

        assert overview["A1"].value == "字段"
        assert overview["B2"].value == "项目日报"
        assert overview["B6"].value == "完成 xlsx 和 pdf 导出。"
        assert tasks["A2"].value == "已完成"
        assert tasks["C2"].value == "实现 Excel 导出"

    asyncio.run(run())


def test_pdf_export_service_creates_pdf(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))

    async def run() -> None:
        service = PdfExportService()
        result = await service.export(_build_report(), "pdf")

        assert result.export_type == "pdf"
        assert result.file_path.endswith(".pdf")

        content = Path(result.file_path).read_bytes()
        assert content.startswith(b"%PDF-")
        assert b"/Type /Catalog" in content
        assert b"ReportLab" in content
        assert len(content) > 10_000

    asyncio.run(run())


def _build_report() -> ReportContent:
    return ReportContent(
        report_type="daily",
        title="项目日报",
        date=date(2026, 7, 22),
        summary="完成 xlsx 和 pdf 导出。",
        completed_tasks=[
            TaskItem(
                id="task-1",
                title="实现 Excel 导出",
                description="生成可打开的 xlsx 文件。",
                status="completed",
                progress=100,
                confidence=0.95,
                user_confirmed=True,
            )
        ],
        in_progress_tasks=[
            TaskItem(
                id="task-2",
                title="完善 PDF 样式",
                status="in_progress",
                progress=60,
            )
        ],
        problems=["暂无真实模板样式"],
        solutions=["先提供基础文本导出"],
        next_plan=["接入前端下载按钮"],
    )

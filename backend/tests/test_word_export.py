from __future__ import annotations

import asyncio
from datetime import date
from zipfile import ZipFile

from app.schemas.report import ReportContent, TaskItem
from app.services.export.word import WordExportService


def test_word_export_service_creates_docx(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))

    async def run() -> None:
        service = WordExportService()
        result = await service.export(
            ReportContent(
                report_type="daily",
                title="项目日报",
                date=date(2026, 7, 16),
                summary="完成基础导出联调。",
                completed_tasks=[
                    TaskItem(
                        id="task-1",
                        title="实现 Word 导出",
                        description="生成可打开的 docx 文件。",
                        status="completed",
                        progress=100,
                    )
                ],
                next_plan=["接入模板填充"],
            ),
            "docx",
        )

        assert result.export_type == "docx"
        assert result.file_path.endswith(".docx")

        with ZipFile(result.file_path) as docx:
            assert "word/document.xml" in docx.namelist()
            document_xml = docx.read("word/document.xml").decode("utf-8")

        assert "项目日报" in document_xml
        assert "完成基础导出联调" in document_xml
        assert "实现 Word 导出" in document_xml

    asyncio.run(run())

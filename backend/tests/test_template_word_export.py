from __future__ import annotations

import asyncio
from datetime import date
from zipfile import ZipFile

from app.schemas.report import ReportContent, TaskItem
from app.services.export.template_word import TemplateWordExportService
from app.services.export.word import _write_docx


def test_template_word_export_replaces_placeholders(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    template_path = tmp_path / "daily_report_template.docx"
    _write_docx(
        template_path,
        """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{{title}}</w:t></w:r></w:p>
    <w:p><w:r><w:t>日期：{{date}}</w:t></w:r></w:p>
    <w:p><w:r><w:t>{{summary}}</w:t></w:r></w:p>
    <w:p><w:r><w:t>{{completed_tasks}}</w:t></w:r></w:p>
    <w:p><w:r><w:t>{{next_plan}}</w:t></w:r></w:p>
  </w:body>
</w:document>
""",
    )

    async def run() -> None:
        service = TemplateWordExportService()
        result = await service.export_with_template(
            ReportContent(
                report_type="daily",
                title="项目日报",
                date=date(2026, 7, 16),
                summary="完成模板填充导出。",
                completed_tasks=[
                    TaskItem(
                        id="task-1",
                        title="实现模板导出",
                        description="替换 Word 占位符。",
                        status="completed",
                        progress=100,
                    )
                ],
                next_plan=["接入真实报表数据"],
            ),
            "docx",
            str(template_path),
        )

        with ZipFile(result.file_path) as docx:
            document_xml = docx.read("word/document.xml").decode("utf-8")

        assert "{{title}}" not in document_xml
        assert "{{completed_tasks}}" not in document_xml
        assert "项目日报" in document_xml
        assert "完成模板填充导出" in document_xml
        assert "实现模板导出" in document_xml
        assert "接入真实报表数据" in document_xml

    asyncio.run(run())

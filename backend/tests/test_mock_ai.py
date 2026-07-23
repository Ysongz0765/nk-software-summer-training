from __future__ import annotations

import asyncio
from datetime import date

from app.schemas.report import ReportGenerationRequest, TaskExtractionInput
from app.services.ai.mock import MockAIReportService


def test_mock_ai_service_returns_structured_report() -> None:
    async def run() -> None:
        service = MockAIReportService()
        tasks = await service.extract_tasks(
            TaskExtractionInput(
                source_text="完成数据库表设计\n正在联调 OCR 识别\n计划补充真实 AI 配置"
            )
        )
        assert [task.status for task in tasks] == ["completed", "in_progress", "pending"]
        assert tasks[0].title == "完成数据库表设计"

        missing = await service.check_missing_information(tasks)
        assert "task_confirmation" in missing.missing_fields

        report = await service.generate_report(
            ReportGenerationRequest(
                report_type="daily",
                title="Demo",
                report_date=date(2026, 7, 16),
                tasks=tasks,
            )
        )
        assert report.title == "Demo"
        assert report.completed_tasks
        assert report.in_progress_tasks
        assert report.missing_fields

    asyncio.run(run())

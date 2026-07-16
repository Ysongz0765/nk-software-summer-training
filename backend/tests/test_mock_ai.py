from __future__ import annotations

import asyncio
from datetime import date

from app.schemas.report import ReportGenerationRequest, TaskExtractionInput
from app.services.ai.mock import MockAIReportService


def test_mock_ai_service_returns_structured_report() -> None:
    async def run() -> None:
        service = MockAIReportService()
        tasks = await service.extract_tasks(TaskExtractionInput(source_text="mock"))
        assert len(tasks) >= 3
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

    asyncio.run(run())

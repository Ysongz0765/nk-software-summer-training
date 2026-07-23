from __future__ import annotations

import asyncio
from datetime import date

import pytest

from app.core.exceptions import AIServiceUnavailableError
from app.schemas.report import ReportGenerationRequest, TaskExtractionInput, TaskItem
from app.services.ai.deepseek import DeepSeekAIReportService


class StubDeepSeekAIReportService(DeepSeekAIReportService):
    def __init__(self, responses: list[dict[str, object]]) -> None:
        super().__init__(api_key="sk-test")
        self._responses = responses

    async def _chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, object]:
        return self._responses.pop(0)


def test_deepseek_service_validates_structured_task_response() -> None:
    async def run() -> None:
        service = StubDeepSeekAIReportService(
            [
                {
                    "tasks": [
                        {
                            "id": "ai-task-1",
                            "title": "完成 DeepSeek 接入",
                            "status": "completed",
                            "progress": 100,
                            "confidence": 0.95,
                        }
                    ]
                }
            ]
        )

        tasks = await service.extract_tasks(TaskExtractionInput(source_text="完成 DeepSeek 接入"))

        assert tasks[0].title == "完成 DeepSeek 接入"
        assert tasks[0].source == "ai"

    asyncio.run(run())


def test_deepseek_service_rejects_invalid_task_response() -> None:
    async def run() -> None:
        service = StubDeepSeekAIReportService(
            [
                {
                    "tasks": [
                        {
                            "id": "ai-task-1",
                            "title": "进度越界",
                            "status": "in_progress",
                            "progress": 120,
                            "confidence": 0.8,
                        }
                    ]
                }
            ]
        )

        with pytest.raises(AIServiceUnavailableError):
            await service.extract_tasks(TaskExtractionInput(source_text="进度越界"))

    asyncio.run(run())


def test_deepseek_service_validates_report_response() -> None:
    async def run() -> None:
        task = TaskItem(
            id="task-1",
            title="完成 OCR 接入",
            status="completed",
            progress=100,
            confidence=0.9,
        )
        service = StubDeepSeekAIReportService(
            [
                {
                    "report": {
                        "report_type": "daily",
                        "title": "日报",
                        "date": "2026-07-23",
                        "summary": "完成 DeepSeek 和 OCR 接入。",
                        "completed_tasks": [task.model_dump(mode="json")],
                        "in_progress_tasks": [],
                        "problems": [],
                        "solutions": [],
                        "next_plan": ["继续联调前端流程"],
                        "custom_fields": {},
                        "missing_fields": [],
                        "style": "concise",
                    }
                }
            ]
        )

        report = await service.generate_report(
            ReportGenerationRequest(
                report_type="daily",
                title="日报",
                report_date=date(2026, 7, 23),
                tasks=[task],
            )
        )

        assert report.summary == "完成 DeepSeek 和 OCR 接入。"
        assert report.custom_fields["generated_by"] == "DeepSeekAIReportService"

    asyncio.run(run())

from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.report import (
    MissingInformationResult,
    ReportContent,
    ReportGenerationRequest,
    TaskExtractionInput,
    TaskItem,
)
from app.services.ai.base import AIReportService


class MockAIReportService(AIReportService):
    async def extract_tasks(self, input_data: TaskExtractionInput) -> list[TaskItem]:
        return [
            TaskItem(
                id="task-1",
                title="完成数据库表设计",
                description="根据需求整理核心数据表和字段。",
                status="completed",
                progress=100,
                end_time=datetime.now(UTC),
                confidence=0.96,
                source="mock",
                user_confirmed=True,
            ),
            TaskItem(
                id="task-2",
                title="完成后端健康检查接口",
                description="提供统一的 API 健康检查能力。",
                status="in_progress",
                progress=70,
                start_time=datetime.now(UTC),
                confidence=0.93,
                source="mock",
            ),
            TaskItem(
                id="task-3",
                title="整理项目需求文档",
                description="补齐 README、架构和接口说明。",
                status="pending",
                progress=20,
                confidence=0.88,
                source="mock",
            ),
        ]

    async def check_missing_information(self, tasks: list[TaskItem]) -> MissingInformationResult:
        missing = ["report_owner", "target_date", "verification_notes"]
        questions = [
            "请确认报表负责人。",
            "请补充报表截止日期。",
            "请补充验收说明。",
        ]
        return MissingInformationResult(
            missing_fields=missing,
            questions=questions,
            confidence=0.82,
        )

    async def generate_report(self, request: ReportGenerationRequest) -> ReportContent:
        completed = [task for task in request.tasks if task.status == "completed"]
        active = [task for task in request.tasks if task.status != "completed"]
        return ReportContent(
            report_type=request.report_type,
            title=request.title,
            date=request.report_date,
            summary="这是一个用于联调的 Mock 报表内容。",
            completed_tasks=completed,
            in_progress_tasks=active,
            problems=["暂无真实 AI 数据接入。"],
            solutions=["当前使用 MockAIReportService。"],
            next_plan=["接入真实 OCR。", "接入真实大模型。"],
            custom_fields={"template_id": request.template_id, "style": request.style},
            missing_fields=[],
            style=request.style,
        )

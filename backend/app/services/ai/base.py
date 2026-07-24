from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.report import (
    MissingInformationResult,
    ReportContent,
    ReportGenerationRequest,
    TaskExtractionInput,
    TaskItem,
)


class AIReportService(ABC):
    @abstractmethod
    async def extract_tasks(self, input_data: TaskExtractionInput) -> list[TaskItem]:
        raise NotImplementedError

    @abstractmethod
    async def check_missing_information(
        self,
        tasks: list[TaskItem],
        template_fields: list[str] | None = None,
        source_data: dict[str, object] | None = None,
    ) -> MissingInformationResult:
        raise NotImplementedError

    @abstractmethod
    async def generate_report(self, request: ReportGenerationRequest) -> ReportContent:
        raise NotImplementedError

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.report import ExportResult, ReportContent


class ExportService(ABC):
    @abstractmethod
    async def export(self, report: ReportContent, export_type: str) -> ExportResult:
        raise NotImplementedError

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.report import TemplateParseResult


class TemplateService(ABC):
    @abstractmethod
    async def parse_template(self, file_path: str) -> TemplateParseResult:
        raise NotImplementedError

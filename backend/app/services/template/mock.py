from __future__ import annotations

from app.schemas.report import TemplateParseResult
from app.services.template.base import TemplateService


class MockTemplateService(TemplateService):
    async def parse_template(self, file_path: str) -> TemplateParseResult:
        return TemplateParseResult(
            template_type="daily",
            fields=["title", "summary", "completed_tasks", "next_plan"],
            description=f"Mock template parsed from {file_path}",
            raw_content={"source": "mock", "path": file_path},
        )

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import get_settings
from app.schemas.report import ExportResult, ReportContent
from app.services.export.base import ExportService


class MockExportService(ExportService):
    async def export(self, report: ReportContent, export_type: str) -> ExportResult:
        settings = get_settings()
        export_dir = Path(settings.storage_root) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", report.title).strip("_") or "report"
        file_path = export_dir / f"{safe_title}-{export_type}.txt"
        file_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return ExportResult(
            export_type=export_type,
            file_path=str(file_path),
            status="success",
            download_url=f"/storage/exports/{file_path.name}",
        )

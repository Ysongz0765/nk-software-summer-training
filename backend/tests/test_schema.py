from __future__ import annotations

from datetime import date

from app.schemas.report import ReportContent, TaskItem


def test_report_content_schema_round_trip() -> None:
    payload = ReportContent(
        report_type="daily",
        title="Weekly Review",
        date=date(2026, 7, 16),
        summary="Mock summary",
        completed_tasks=[TaskItem(id="1", title="done", status="completed", progress=100)],
    )
    data = payload.model_dump()
    assert data["title"] == "Weekly Review"
    assert data["completed_tasks"][0]["status"] == "completed"

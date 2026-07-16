from __future__ import annotations

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository):
    def create(self, report: Report) -> Report:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get(self, report_id: int) -> Report | None:
        return self.db.get(Report, report_id)

from __future__ import annotations

from sqlalchemy import desc

from app.models.report import ExportRecord, Report, ReportVersion
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository):
    def create(self, report: Report) -> Report:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get(self, report_id: int) -> Report | None:
        return self.db.get(Report, report_id)

    def list_reports(
        self,
        user_id: int | None = None,
        project_id: int | None = None,
    ) -> list[Report]:
        query = self.db.query(Report)
        if user_id is not None:
            query = query.filter(Report.user_id == user_id)
        elif project_id is None:
            query = query.filter(Report.project_id.is_(None))
        if project_id is not None:
            query = query.filter(Report.project_id == project_id)
        return list(query.order_by(desc(Report.created_at), desc(Report.id)).all())

    def save(self, report: Report) -> Report:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def delete(self, report: Report) -> None:
        self.db.delete(report)
        self.db.commit()

    def next_version_number(self, report_id: int) -> int:
        current = (
            self.db.query(ReportVersion)
            .filter(ReportVersion.report_id == report_id)
            .order_by(desc(ReportVersion.version_number))
            .first()
        )
        return (current.version_number if current else 0) + 1

    def create_version(
        self,
        report_id: int,
        content: dict[str, object],
        change_note: str | None = None,
    ) -> ReportVersion:
        version = ReportVersion(
            report_id=report_id,
            version_number=self.next_version_number(report_id),
            content=content,
            change_note=change_note,
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def list_versions(self, report_id: int) -> list[ReportVersion]:
        return list(
            self.db.query(ReportVersion)
            .filter(ReportVersion.report_id == report_id)
            .order_by(desc(ReportVersion.version_number))
            .all()
        )

    def create_export_record(
        self,
        report_id: int,
        project_id: int | None,
        export_type: str,
        file_path: str,
        status: str,
    ) -> ExportRecord:
        record = ExportRecord(
            report_id=report_id,
            project_id=project_id,
            export_type=export_type,
            file_path=file_path,
            status=status,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

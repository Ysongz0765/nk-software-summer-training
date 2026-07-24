from __future__ import annotations

from sqlalchemy import desc

from app.models.file import UploadedFile
from app.models.project import Project, ProjectMember, ProjectMemory, ProjectTask
from app.models.report import Report
from app.models.template import Template
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository):
    def create(self, project: Project) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get(self, project_id: int) -> Project | None:
        return self.db.get(Project, project_id)

    def list_projects(self, user_id: int, status: str | None = None) -> list[Project]:
        query = self.db.query(Project).filter(Project.user_id == user_id)
        if status:
            query = query.filter(Project.status == status)
        return list(query.order_by(desc(Project.last_activity_at), desc(Project.id)).all())

    def save(self, project: Project) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def file_count(self, project_id: int) -> int:
        return self.db.query(UploadedFile).filter(UploadedFile.project_id == project_id).count()

    def report_count(self, project_id: int) -> int:
        return self.db.query(Report).filter(Report.project_id == project_id).count()

    def task_count(self, project_id: int, status: str | None = None) -> int:
        query = self.db.query(ProjectTask).filter(ProjectTask.project_id == project_id)
        if status:
            query = query.filter(ProjectTask.status == status)
        return query.count()

    def list_tasks(
        self,
        project_id: int,
        status: str | None = None,
        module: str | None = None,
    ) -> list[ProjectTask]:
        query = self.db.query(ProjectTask).filter(ProjectTask.project_id == project_id)
        if status:
            query = query.filter(ProjectTask.status == status)
        if module:
            query = query.filter(ProjectTask.module == module)
        return list(query.order_by(desc(ProjectTask.updated_at), desc(ProjectTask.id)).all())

    def get_task(self, project_id: int, task_id: int) -> ProjectTask | None:
        return (
            self.db.query(ProjectTask)
            .filter(ProjectTask.project_id == project_id, ProjectTask.id == task_id)
            .one_or_none()
        )

    def list_members(self, project_id: int) -> list[ProjectMember]:
        return list(
            self.db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.id)
            .all()
        )

    def get_member(self, project_id: int, member_id: int) -> ProjectMember | None:
        return (
            self.db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.id == member_id)
            .one_or_none()
        )

    def list_files(self, project_id: int, limit: int | None = None) -> list[UploadedFile]:
        query = (
            self.db.query(UploadedFile)
            .filter(UploadedFile.project_id == project_id)
            .order_by(desc(UploadedFile.created_at), desc(UploadedFile.id))
        )
        if limit is not None:
            query = query.limit(limit)
        return list(query.all())

    def list_reports(self, project_id: int, limit: int | None = None) -> list[Report]:
        query = (
            self.db.query(Report)
            .filter(Report.project_id == project_id)
            .order_by(desc(Report.report_date), desc(Report.created_at), desc(Report.id))
        )
        if limit is not None:
            query = query.limit(limit)
        return list(query.all())

    def list_templates(self, project_id: int) -> list[Template]:
        return list(
            self.db.query(Template)
            .filter((Template.project_id.is_(None)) | (Template.project_id == project_id))
            .order_by(Template.project_id.is_(None), Template.id)
            .all()
        )

    def list_memories(
        self,
        project_id: int,
        limit: int | None = None,
    ) -> list[ProjectMemory]:
        query = (
            self.db.query(ProjectMemory)
            .filter(ProjectMemory.project_id == project_id)
            .order_by(desc(ProjectMemory.is_user_confirmed), desc(ProjectMemory.updated_at))
        )
        if limit is not None:
            query = query.limit(limit)
        return list(query.all())

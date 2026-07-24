from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.file import UploadedFile
from app.models.project import Project, ProjectMember, ProjectMemory, ProjectTask
from app.models.report import Report
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.schemas.project import (
    ProjectContextRead,
    ProjectFileRead,
    ProjectListItem,
    ProjectMemberRead,
    ProjectMemoryRead,
    ProjectRead,
    ProjectReference,
    ProjectReportRead,
    ProjectSummarySuggestion,
    ProjectTaskRead,
)
from app.schemas.report import TaskItem


def ensure_project_access(db: Session, project_id: int, user: User | None) -> Project:
    if user is None:
        raise PermissionDeniedError("authentication required")
    project = db.get(Project, project_id)
    if project is None:
        raise ResourceNotFoundError("project not found")
    if project.user_id != user.id:
        raise PermissionDeniedError("project access denied")
    return project


def touch_project(db: Session, project: Project, commit: bool = True) -> None:
    project.last_activity_at = datetime.now(UTC)
    db.add(project)
    if commit:
        db.commit()


def project_to_read(project: Project) -> ProjectRead:
    return ProjectRead(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        current_stage=project.current_stage,
        start_date=project.start_date,
        end_date=project.end_date,
        tech_stack=list(project.tech_stack or []),
        background_summary=project.background_summary,
        last_activity_at=project.last_activity_at,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def project_to_reference(project: Project | None) -> ProjectReference | None:
    if project is None:
        return None
    return ProjectReference(
        id=project.id,
        name=project.name,
        status=project.status,
        current_stage=project.current_stage,
    )


def project_to_list_item(project: Project, repository: ProjectRepository) -> ProjectListItem:
    return ProjectListItem(
        **project_to_read(project).model_dump(),
        file_count=repository.file_count(project.id),
        report_count=repository.report_count(project.id),
        task_total=repository.task_count(project.id),
        task_completed=repository.task_count(project.id, status="completed"),
    )


def task_to_read(task: ProjectTask) -> ProjectTaskRead:
    return ProjectTaskRead(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        module=task.module,
        status=task.status,
        priority=task.priority,
        owner=task.owner,
        start_date=task.start_date,
        due_date=task.due_date,
        completed_at=task.completed_at,
        source_type=task.source_type,
        confidence=task.confidence,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def member_to_read(member: ProjectMember) -> ProjectMemberRead:
    return ProjectMemberRead(
        id=member.id,
        project_id=member.project_id,
        name=member.name,
        role=member.role,
        responsibility=member.responsibility,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


def memory_to_read(memory: ProjectMemory) -> ProjectMemoryRead:
    return ProjectMemoryRead(
        id=memory.id,
        project_id=memory.project_id,
        memory_type=memory.memory_type,
        content=memory.content,
        source_ids=list(memory.source_ids or []),
        is_user_confirmed=memory.is_user_confirmed,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


def file_to_read(file_record: UploadedFile) -> ProjectFileRead:
    return ProjectFileRead(
        id=file_record.id,
        user_id=file_record.user_id,
        project_id=file_record.project_id,
        original_name=file_record.original_name,
        stored_name=file_record.stored_name,
        file_type=file_record.file_type,
        file_size=file_record.file_size,
        storage_path=file_record.storage_path,
        status=file_record.status,
        created_at=file_record.created_at,
    )


def report_to_project_read(report: Report) -> ProjectReportRead:
    content = dict(report.content or {})
    completed = content.get("completed_tasks")
    active = content.get("in_progress_tasks")
    task_count = _list_len(completed) + _list_len(active)
    return ProjectReportRead(
        id=report.id,
        project_id=report.project_id,
        report_type=report.report_type,
        title=report.title,
        report_date=report.report_date,
        status=report.status,
        task_count=task_count,
    )


def build_project_context(db: Session, project: Project) -> ProjectContextRead:
    repository = ProjectRepository(db)
    recent_tasks = repository.list_tasks(project.id)[:10]
    completed_tasks = repository.list_tasks(project.id, status="completed")[:10]
    in_progress_tasks = repository.list_tasks(project.id, status="in_progress")[:10]
    blocked_tasks = repository.list_tasks(project.id, status="blocked")[:10]
    memories = repository.list_memories(project.id, limit=20)

    return ProjectContextRead(
        project=project_to_read(project),
        members=[member_to_read(member) for member in repository.list_members(project.id)],
        recent_tasks=[task_to_read(task) for task in recent_tasks],
        completed_tasks=[task_to_read(task) for task in completed_tasks],
        in_progress_tasks=[task_to_read(task) for task in in_progress_tasks],
        blocked_tasks=[task_to_read(task) for task in blocked_tasks],
        recent_files=[
            file_to_read(file_record)
            for file_record in repository.list_files(project.id, 10)
        ],
        recent_reports=[
            report_to_project_read(report)
            for report in repository.list_reports(project.id, 10)
        ],
        project_memories=[memory_to_read(memory) for memory in memories],
        background_summary=_background_summary(project, memories),
    )


def build_ai_project_context(
    db: Session,
    project: Project,
    start_date: date | None = None,
    end_date: date | None = None,
    file_ids: list[int] | None = None,
    task_ids: list[int] | None = None,
    user_notes: str = "",
) -> dict[str, object]:
    selected_files = _selected_project_files(db, project.id, file_ids or [])
    selected_tasks = _selected_project_tasks(db, project.id, task_ids or [])
    recent_tasks = _recent_project_tasks(db, project.id)
    completed_tasks = [task for task in recent_tasks if task.status == "completed"]
    in_progress_tasks = [task for task in recent_tasks if task.status == "in_progress"]
    blocked_tasks = [task for task in recent_tasks if task.status == "blocked"]
    memories = ProjectRepository(db).list_memories(project.id, limit=20)
    members = ProjectRepository(db).list_members(project.id)
    recent_files = selected_files or ProjectRepository(db).list_files(project.id, limit=10)
    recent_reports = _recent_project_reports(db, project.id, start_date, end_date)

    goal = _first_memory_content(memories, "goal") or project.description or ""
    return {
        "project_profile": {
            "id": project.id,
            "name": project.name,
            "description": project.description or "",
            "project_type": project.project_type or "",
            "goal": goal,
            "current_stage": project.current_stage or "",
            "tech_stack": list(project.tech_stack or []),
            "background_summary": _background_summary(project, memories),
        },
        "members": [member_to_read(member).model_dump(mode="json") for member in members],
        "report_period": _report_period(start_date, end_date),
        "recent_tasks": [task_to_read(task).model_dump(mode="json") for task in recent_tasks],
        "selected_tasks": [task_to_read(task).model_dump(mode="json") for task in selected_tasks],
        "completed_tasks": [task_to_read(task).model_dump(mode="json") for task in completed_tasks],
        "in_progress_tasks": [
            task_to_read(task).model_dump(mode="json") for task in in_progress_tasks
        ],
        "blocked_tasks": [task_to_read(task).model_dump(mode="json") for task in blocked_tasks],
        "recent_files": [
            file_to_read(file_record).model_dump(mode="json")
            for file_record in recent_files
        ],
        "previous_report_summary": _previous_report_summary(recent_reports),
        "recent_reports": [
            report_to_project_read(report).model_dump(mode="json") for report in recent_reports
        ],
        "project_memories": [memory_to_read(memory).model_dump(mode="json") for memory in memories],
        "user_notes": user_notes,
    }


def project_tasks_to_task_items(tasks: list[ProjectTask]) -> list[TaskItem]:
    return [
        TaskItem(
            id=f"project-task-{task.id}",
            title=task.title,
            description=task.description,
            status=task.status,
            progress=_progress_for_project_task(task.status),
            start_time=None,
            end_time=task.completed_at,
            evidence_file_ids=[],
            confidence=task.confidence if task.confidence is not None else 1.0,
            source=task.source_type or "project",
            user_confirmed=True,
        )
        for task in tasks
    ]


def selected_project_tasks(db: Session, project_id: int, task_ids: list[int]) -> list[ProjectTask]:
    return _selected_project_tasks(db, project_id, task_ids)


def generate_project_summary(
    project: Project,
    context: ProjectContextRead,
) -> ProjectSummarySuggestion:
    completed_titles = [task.title for task in context.completed_tasks[:5]]
    problem_titles = [task.title for task in context.blocked_tasks[:5]]
    stage = project.current_stage or _first_memory_text(context.project_memories, "current_stage")
    tech_stack = list(project.tech_stack or [])

    summary_parts = [
        f"项目「{project.name}」",
        f"当前处于「{stage}」阶段" if stage else "当前阶段尚未明确",
    ]
    if completed_titles:
        summary_parts.append(f"近期已完成：{'、'.join(completed_titles)}")
    if problem_titles:
        summary_parts.append(f"当前阻塞：{'、'.join(problem_titles)}")
    if context.recent_files:
        summary_parts.append(f"已沉淀 {len(context.recent_files)} 份近期项目材料")

    return ProjectSummarySuggestion(
        generated_summary="；".join(summary_parts) + "。",
        suggested_current_stage=stage,
        suggested_tech_stack=tech_stack,
        suggested_completed_work=completed_titles,
        suggested_current_problems=problem_titles,
    )


def _selected_project_files(
    db: Session,
    project_id: int,
    file_ids: list[int],
) -> list[UploadedFile]:
    if not file_ids:
        return []
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.project_id == project_id, UploadedFile.id.in_(file_ids))
        .order_by(desc(UploadedFile.created_at), desc(UploadedFile.id))
        .all()
    )
    if {file_record.id for file_record in files} != set(file_ids):
        raise ResourceNotFoundError("project file not found")
    return list(files)


def _selected_project_tasks(
    db: Session,
    project_id: int,
    task_ids: list[int],
) -> list[ProjectTask]:
    if not task_ids:
        return []
    tasks = (
        db.query(ProjectTask)
        .filter(ProjectTask.project_id == project_id, ProjectTask.id.in_(task_ids))
        .order_by(desc(ProjectTask.updated_at), desc(ProjectTask.id))
        .all()
    )
    if {task.id for task in tasks} != set(task_ids):
        raise ResourceNotFoundError("project task not found")
    return list(tasks)


def _recent_project_tasks(db: Session, project_id: int) -> list[ProjectTask]:
    return list(
        db.query(ProjectTask)
        .filter(ProjectTask.project_id == project_id)
        .order_by(desc(ProjectTask.updated_at), desc(ProjectTask.id))
        .limit(20)
        .all()
    )


def _recent_project_reports(
    db: Session,
    project_id: int,
    start_date: date | None,
    end_date: date | None,
) -> list[Report]:
    query = db.query(Report).filter(Report.project_id == project_id)
    if start_date is not None:
        query = query.filter(Report.report_date >= start_date)
    if end_date is not None:
        query = query.filter(Report.report_date <= end_date)
    return list(query.order_by(desc(Report.report_date), desc(Report.id)).limit(10).all())


def _background_summary(project: Project, memories: list[ProjectMemory]) -> str:
    confirmed_background = _first_memory_content(memories, "background", confirmed_only=True)
    if confirmed_background:
        return confirmed_background
    return project.background_summary or _first_memory_content(memories, "background") or ""


def _first_memory_content(
    memories: list[ProjectMemory],
    memory_type: str,
    confirmed_only: bool = False,
) -> str | None:
    for memory in memories:
        if memory.memory_type != memory_type:
            continue
        if confirmed_only and not memory.is_user_confirmed:
            continue
        if memory.content.strip():
            return memory.content.strip()
    return None


def _first_memory_text(memories: list[ProjectMemoryRead], memory_type: str) -> str | None:
    for memory in memories:
        if memory.memory_type == memory_type and memory.content.strip():
            return memory.content.strip()
    return None


def _previous_report_summary(reports: list[Report]) -> str:
    for report in reports:
        content = dict(report.content or {})
        summary = content.get("summary")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
    return ""


def _report_period(start_date: date | None, end_date: date | None) -> str:
    if start_date and end_date:
        return f"{start_date.isoformat()} 至 {end_date.isoformat()}"
    if start_date:
        return start_date.isoformat()
    if end_date:
        return end_date.isoformat()
    return ""


def _progress_for_project_task(status: str) -> int:
    return {
        "completed": 100,
        "in_progress": 70,
        "pending": 20,
        "blocked": 40,
    }.get(status, 50)


def _list_len(value: object) -> int:
    return len(value) if isinstance(value, list) else 0

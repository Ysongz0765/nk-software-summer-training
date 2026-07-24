from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.models.project import Project, ProjectMember, ProjectTask
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.schemas.common import ApiResponse
from app.schemas.project import (
    ProjectContextRead,
    ProjectCreate,
    ProjectFileRead,
    ProjectListItem,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberUpdate,
    ProjectRead,
    ProjectSummarySuggestion,
    ProjectTaskCreate,
    ProjectTaskRead,
    ProjectTaskUpdate,
    ProjectUpdate,
)
from app.services.project_context import (
    build_project_context,
    ensure_project_access,
    file_to_read,
    generate_project_summary,
    member_to_read,
    project_to_list_item,
    project_to_read,
    task_to_read,
    touch_project,
)

router = APIRouter()


@router.post("", response_model=ApiResponse[ProjectRead])
async def create_project(
    payload: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectRead]:
    now = datetime.now(UTC)
    project = Project(
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description,
        project_type=payload.project_type,
        status=payload.status,
        current_stage=payload.current_stage,
        start_date=payload.start_date,
        end_date=payload.end_date,
        tech_stack=_clean_tech_stack(payload.tech_stack),
        background_summary=payload.background_summary,
        last_activity_at=now,
    )
    project = ProjectRepository(db).create(project)
    return ApiResponse(data=project_to_read(project))


@router.get("", response_model=ApiResponse[list[ProjectListItem]])
async def list_projects(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> ApiResponse[list[ProjectListItem]]:
    repository = ProjectRepository(db)
    projects = repository.list_projects(current_user.id, status=status_filter)
    return ApiResponse(data=[project_to_list_item(project, repository) for project in projects])


@router.get("/{project_id}", response_model=ApiResponse[ProjectListItem])
async def get_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectListItem]:
    project = ensure_project_access(db, project_id, current_user)
    return ApiResponse(data=project_to_list_item(project, ProjectRepository(db)))


@router.patch("/{project_id}", response_model=ApiResponse[ProjectRead])
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectRead]:
    project = ensure_project_access(db, project_id, current_user)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and isinstance(data["name"], str):
        project.name = data["name"].strip()
    for field in {
        "description",
        "project_type",
        "status",
        "current_stage",
        "start_date",
        "end_date",
        "background_summary",
    }:
        if field in data:
            setattr(project, field, data[field])
    if "tech_stack" in data:
        project.tech_stack = _clean_tech_stack(data["tech_stack"])
    touch_project(db, project, commit=False)
    project = ProjectRepository(db).save(project)
    return ApiResponse(data=project_to_read(project))


@router.put("/{project_id}", response_model=ApiResponse[ProjectRead])
async def replace_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectRead]:
    return await update_project(project_id, payload, db, current_user)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[dict[str, object]],
)
async def archive_project(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict[str, object]]:
    project = ensure_project_access(db, project_id, current_user)
    project.status = "archived"
    touch_project(db, project, commit=False)
    ProjectRepository(db).save(project)
    return ApiResponse(data={"id": project_id, "status": "archived"})


@router.post("/{project_id}/tasks", response_model=ApiResponse[ProjectTaskRead])
async def create_project_task(
    project_id: int,
    payload: ProjectTaskCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectTaskRead]:
    project = ensure_project_access(db, project_id, current_user)
    task = ProjectTask(
        project_id=project.id,
        title=payload.title.strip(),
        description=payload.description,
        module=payload.module,
        status=payload.status,
        priority=payload.priority,
        owner=payload.owner,
        start_date=payload.start_date,
        due_date=payload.due_date,
        completed_at=datetime.now(UTC) if payload.status == "completed" else None,
        source_type=payload.source_type,
        confidence=payload.confidence,
    )
    db.add(task)
    touch_project(db, project, commit=False)
    db.commit()
    db.refresh(task)
    return ApiResponse(data=task_to_read(task))


@router.get("/{project_id}/tasks", response_model=ApiResponse[list[ProjectTaskRead]])
async def list_project_tasks(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    module: str | None = None,
) -> ApiResponse[list[ProjectTaskRead]]:
    project = ensure_project_access(db, project_id, current_user)
    tasks = ProjectRepository(db).list_tasks(
        project.id,
        status=status_filter,
        module=module,
    )
    return ApiResponse(data=[task_to_read(task) for task in tasks])


@router.get("/{project_id}/tasks/{task_id}", response_model=ApiResponse[ProjectTaskRead])
async def get_project_task(
    project_id: int,
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectTaskRead]:
    ensure_project_access(db, project_id, current_user)
    task = ProjectRepository(db).get_task(project_id, task_id)
    if task is None:
        raise ResourceNotFoundError("project task not found")
    return ApiResponse(data=task_to_read(task))


@router.patch("/{project_id}/tasks/{task_id}", response_model=ApiResponse[ProjectTaskRead])
async def update_project_task(
    project_id: int,
    task_id: int,
    payload: ProjectTaskUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectTaskRead]:
    project = ensure_project_access(db, project_id, current_user)
    task = ProjectRepository(db).get_task(project.id, task_id)
    if task is None:
        raise ResourceNotFoundError("project task not found")

    data = payload.model_dump(exclude_unset=True)
    if "title" in data and isinstance(data["title"], str):
        task.title = data["title"].strip()
    for field in {
        "description",
        "module",
        "status",
        "priority",
        "owner",
        "start_date",
        "due_date",
        "source_type",
        "confidence",
    }:
        if field in data:
            setattr(task, field, data[field])
    if "status" in data:
        task.completed_at = datetime.now(UTC) if task.status == "completed" else None

    db.add(task)
    touch_project(db, project, commit=False)
    db.commit()
    db.refresh(task)
    return ApiResponse(data=task_to_read(task))


@router.delete(
    "/{project_id}/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[dict[str, int]],
)
async def delete_project_task(
    project_id: int,
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict[str, int]]:
    project = ensure_project_access(db, project_id, current_user)
    task = ProjectRepository(db).get_task(project.id, task_id)
    if task is None:
        raise ResourceNotFoundError("project task not found")
    db.delete(task)
    touch_project(db, project, commit=False)
    db.commit()
    return ApiResponse(data={"id": task_id})


@router.post("/{project_id}/members", response_model=ApiResponse[ProjectMemberRead])
async def create_project_member(
    project_id: int,
    payload: ProjectMemberCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectMemberRead]:
    project = ensure_project_access(db, project_id, current_user)
    member = ProjectMember(
        project_id=project.id,
        name=payload.name.strip(),
        role=payload.role,
        responsibility=payload.responsibility,
    )
    db.add(member)
    touch_project(db, project, commit=False)
    db.commit()
    db.refresh(member)
    return ApiResponse(data=member_to_read(member))


@router.get("/{project_id}/members", response_model=ApiResponse[list[ProjectMemberRead]])
async def list_project_members(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[ProjectMemberRead]]:
    project = ensure_project_access(db, project_id, current_user)
    members = ProjectRepository(db).list_members(project.id)
    return ApiResponse(data=[member_to_read(member) for member in members])


@router.patch("/{project_id}/members/{member_id}", response_model=ApiResponse[ProjectMemberRead])
async def update_project_member(
    project_id: int,
    member_id: int,
    payload: ProjectMemberUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectMemberRead]:
    project = ensure_project_access(db, project_id, current_user)
    member = ProjectRepository(db).get_member(project.id, member_id)
    if member is None:
        raise ResourceNotFoundError("project member not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and isinstance(data["name"], str):
        member.name = data["name"].strip()
    for field in {"role", "responsibility"}:
        if field in data:
            setattr(member, field, data[field])

    db.add(member)
    touch_project(db, project, commit=False)
    db.commit()
    db.refresh(member)
    return ApiResponse(data=member_to_read(member))


@router.delete(
    "/{project_id}/members/{member_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[dict[str, int]],
)
async def delete_project_member(
    project_id: int,
    member_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[dict[str, int]]:
    project = ensure_project_access(db, project_id, current_user)
    member = ProjectRepository(db).get_member(project.id, member_id)
    if member is None:
        raise ResourceNotFoundError("project member not found")
    db.delete(member)
    touch_project(db, project, commit=False)
    db.commit()
    return ApiResponse(data={"id": member_id})


@router.get("/{project_id}/files", response_model=ApiResponse[list[ProjectFileRead]])
async def list_project_files(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[ProjectFileRead]]:
    project = ensure_project_access(db, project_id, current_user)
    files = ProjectRepository(db).list_files(project.id)
    return ApiResponse(data=[file_to_read(file_record) for file_record in files])


@router.get("/{project_id}/context", response_model=ApiResponse[ProjectContextRead])
async def get_project_context(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectContextRead]:
    project = ensure_project_access(db, project_id, current_user)
    return ApiResponse(data=build_project_context(db, project))


@router.post(
    "/{project_id}/generate-summary",
    response_model=ApiResponse[ProjectSummarySuggestion],
)
async def generate_summary(
    project_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ProjectSummarySuggestion]:
    project = ensure_project_access(db, project_id, current_user)
    context = build_project_context(db, project)
    return ApiResponse(data=generate_project_summary(project, context))


def _clean_tech_stack(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text or text in seen:
            continue
        cleaned.append(text)
        seen.add(text)
    return cleaned

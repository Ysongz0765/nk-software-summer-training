from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


def _blank_to_none(value: object) -> object | None:
    if isinstance(value, str) and not value.strip():
        return None
    return value


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    project_type: str | None = Field(default=None, max_length=64)
    status: str = Field(default="active", max_length=32)
    current_stage: str | None = Field(default=None, max_length=128)
    start_date: date | None = None
    end_date: date | None = None
    tech_stack: list[str] = Field(default_factory=list)
    background_summary: str | None = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def normalize_blank_dates(cls, value: object) -> object | None:
        return _blank_to_none(value)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    project_type: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=32)
    current_stage: str | None = Field(default=None, max_length=128)
    start_date: date | None = None
    end_date: date | None = None
    tech_stack: list[str] | None = None
    background_summary: str | None = None

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def normalize_blank_dates(cls, value: object) -> object | None:
        return _blank_to_none(value)


class ProjectRead(ProjectBase):
    id: int
    user_id: int
    last_activity_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectListItem(ProjectRead):
    file_count: int = 0
    report_count: int = 0
    task_total: int = 0
    task_completed: int = 0


class ProjectReference(BaseModel):
    id: int
    name: str
    status: str
    current_stage: str | None = None


class ProjectTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    module: str | None = Field(default=None, max_length=128)
    status: str = Field(default="pending", max_length=32)
    priority: str | None = Field(default=None, max_length=32)
    owner: str | None = Field(default=None, max_length=128)
    start_date: date | None = None
    due_date: date | None = None
    source_type: str | None = Field(default=None, max_length=64)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("start_date", "due_date", mode="before")
    @classmethod
    def normalize_blank_dates(cls, value: object) -> object | None:
        return _blank_to_none(value)


class ProjectTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    module: str | None = Field(default=None, max_length=128)
    status: str | None = Field(default=None, max_length=32)
    priority: str | None = Field(default=None, max_length=32)
    owner: str | None = Field(default=None, max_length=128)
    start_date: date | None = None
    due_date: date | None = None
    source_type: str | None = Field(default=None, max_length=64)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("start_date", "due_date", mode="before")
    @classmethod
    def normalize_blank_dates(cls, value: object) -> object | None:
        return _blank_to_none(value)


class ProjectTaskRead(ProjectTaskCreate):
    id: int
    project_id: int
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectMemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    role: str | None = Field(default=None, max_length=128)
    responsibility: str | None = None


class ProjectMemberUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    role: str | None = Field(default=None, max_length=128)
    responsibility: str | None = None


class ProjectMemberRead(ProjectMemberCreate):
    id: int
    project_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectMemoryRead(BaseModel):
    id: int
    project_id: int
    memory_type: str
    content: str
    source_ids: list[int] = Field(default_factory=list)
    is_user_confirmed: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectFileRead(BaseModel):
    id: int
    user_id: int | None = None
    project_id: int | None = None
    original_name: str
    stored_name: str
    file_type: str
    file_size: int
    storage_path: str
    status: str
    created_at: datetime | None = None


class ProjectReportRead(BaseModel):
    id: int
    project_id: int | None = None
    report_type: str
    title: str
    report_date: date
    status: str
    task_count: int = 0


class ProjectContextRead(BaseModel):
    project: ProjectRead
    members: list[ProjectMemberRead] = Field(default_factory=list)
    recent_tasks: list[ProjectTaskRead] = Field(default_factory=list)
    completed_tasks: list[ProjectTaskRead] = Field(default_factory=list)
    in_progress_tasks: list[ProjectTaskRead] = Field(default_factory=list)
    blocked_tasks: list[ProjectTaskRead] = Field(default_factory=list)
    recent_files: list[ProjectFileRead] = Field(default_factory=list)
    recent_reports: list[ProjectReportRead] = Field(default_factory=list)
    project_memories: list[ProjectMemoryRead] = Field(default_factory=list)
    background_summary: str = ""


class ProjectSummarySuggestion(BaseModel):
    generated_summary: str
    suggested_current_stage: str | None = None
    suggested_tech_stack: list[str] = Field(default_factory=list)
    suggested_completed_work: list[str] = Field(default_factory=list)
    suggested_current_problems: list[str] = Field(default_factory=list)

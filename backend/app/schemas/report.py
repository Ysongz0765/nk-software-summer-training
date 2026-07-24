from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.project import ProjectReference


class TaskItem(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: str = Field(default="pending")
    progress: int = Field(default=0, ge=0, le=100)
    start_time: datetime | None = None
    end_time: datetime | None = None
    evidence_file_ids: list[int] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = Field(default="mock")
    user_confirmed: bool = Field(default=False)


class ReportContent(BaseModel):
    report_type: str
    title: str
    date: date
    summary: str
    completed_tasks: list[TaskItem] = Field(default_factory=list)
    in_progress_tasks: list[TaskItem] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    solutions: list[str] = Field(default_factory=list)
    next_plan: list[str] = Field(default_factory=list)
    custom_fields: dict[str, object] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    style: str = Field(default="concise")


class OCRResult(BaseModel):
    text: str
    pages: int = 1
    confidence: float = 1.0
    language: str = "zh"


class TemplateParseResult(BaseModel):
    template_type: str
    fields: list[str] = Field(default_factory=list)
    description: str
    raw_content: dict[str, object] = Field(default_factory=dict)


class TaskExtractionInput(BaseModel):
    source_text: str
    report_type: str = "daily"
    context: dict[str, object] = Field(default_factory=dict)


class GitHubProgressAnalysisRequest(BaseModel):
    repo_url: str = Field(min_length=1, max_length=512)
    report_type: str = "daily"
    max_items: int = Field(default=10, ge=1, le=30)


class GitHubProgressAnalysisResult(BaseModel):
    repo_url: str
    repository: dict[str, object] = Field(default_factory=dict)
    source_text: str
    tasks: list[TaskItem] = Field(default_factory=list)


class MissingInformationResult(BaseModel):
    missing_fields: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    confidence: float = 1.0


class MissingInformationRequest(BaseModel):
    tasks: list[TaskItem] = Field(default_factory=list)
    project_id: int | None = None
    template_id: int | None = None
    template_fields: list[str] = Field(default_factory=list)
    source_data: dict[str, object] = Field(default_factory=dict)


class ReportGenerationRequest(BaseModel):
    report_type: str
    title: str = ""
    report_date: date = Field(default_factory=date.today)
    project_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    tasks: list[TaskItem] = Field(default_factory=list)
    file_ids: list[int] = Field(default_factory=list)
    task_ids: list[int] = Field(default_factory=list)
    user_notes: str = ""
    template_id: int | None = None
    template_fields: list[str] = Field(default_factory=list)
    style: str = "concise"
    source_data: dict[str, object] = Field(default_factory=dict)


class ExportResult(BaseModel):
    export_type: str
    file_path: str
    status: str = "success"
    download_url: str | None = None


class ReportSummary(BaseModel):
    id: int
    project_id: int | None = None
    report_type: str
    title: str
    report_date: date
    status: str
    task_count: int = 0


class ReportCreate(BaseModel):
    report_type: str
    title: str
    report_date: date
    project_id: int | None = None
    template_id: int | None = None
    source_data: dict[str, object] = Field(default_factory=dict)


class ReportUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    content: ReportContent | None = None
    source_data: dict[str, object] | None = None


class ReportRead(BaseModel):
    id: int
    user_id: int | None = None
    project_id: int | None = None
    project: ProjectReference | None = None
    template_id: int | None = None
    report_type: str
    title: str
    report_date: date
    status: str
    content: ReportContent
    source_data: dict[str, object] = Field(default_factory=dict)


class ReportVersionRead(BaseModel):
    id: int
    report_id: int
    version_number: int
    content: ReportContent
    change_note: str | None = None
    created_at: datetime | None = None

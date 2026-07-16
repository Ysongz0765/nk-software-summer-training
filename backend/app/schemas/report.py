from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


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


class MissingInformationResult(BaseModel):
    missing_fields: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    confidence: float = 1.0


class ReportGenerationRequest(BaseModel):
    report_type: str
    title: str
    report_date: date
    tasks: list[TaskItem] = Field(default_factory=list)
    template_id: int | None = None
    style: str = "concise"
    source_data: dict[str, object] = Field(default_factory=dict)


class ExportResult(BaseModel):
    export_type: str
    file_path: str
    status: str = "success"
    download_url: str | None = None


class ReportSummary(BaseModel):
    report_type: str
    title: str
    report_date: date
    status: str
    task_count: int = 0


class ReportCreate(BaseModel):
    report_type: str
    title: str
    report_date: date
    template_id: int | None = None
    source_data: dict[str, object] = Field(default_factory=dict)


class ReportUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    content: ReportContent | None = None
    source_data: dict[str, object] | None = None

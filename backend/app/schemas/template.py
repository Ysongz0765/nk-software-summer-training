from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    template_type: str = "daily"
    file_path: str | None = None
    file_id: int | None = None
    field_config: dict[str, object] = Field(default_factory=dict)


class TemplateRead(BaseModel):
    id: int
    user_id: int | None = None
    name: str
    description: str | None = None
    template_type: str
    file_id: int | None = None
    field_config: dict[str, object] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

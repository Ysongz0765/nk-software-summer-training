from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError
from app.models.template import Template
from app.services.template.docx import read_template_text
from app.services.template.render import canonical_field_name

STANDARD_TEMPLATE_FIELDS = {
    "report_type",
    "title",
    "date",
    "summary",
    "completed_tasks",
    "in_progress_tasks",
    "problems",
    "solutions",
    "next_plan",
    "style",
    "missing_fields",
}


@dataclass(frozen=True)
class TemplateContext:
    template_id: int
    name: str
    template_type: str
    fields: list[str]
    field_config: dict[str, object]
    file_path: str | None = None
    render_text: str | None = None

    def model_payload(self) -> dict[str, object]:
        return {
            "id": self.template_id,
            "name": self.name,
            "type": self.template_type,
            "fields": self.fields,
            "render_text": self.render_text,
            "custom_fields": custom_template_fields(self.fields),
        }


def load_template_context(
    db: Session,
    template_id: int | None,
    user_id: int | None = None,
) -> TemplateContext | None:
    if template_id is None:
        return None

    template = db.get(Template, template_id)
    if template is None:
        raise ResourceNotFoundError("template not found")
    if user_id is not None and template.user_id not in {None, user_id}:
        raise PermissionDeniedError("template access denied")

    field_config = template.field_config or {}
    fields = template_fields(field_config)
    file_path = template_file_path(template)
    return TemplateContext(
        template_id=template.id,
        name=template.name,
        template_type=template.template_type,
        fields=fields,
        field_config=field_config,
        file_path=file_path,
        render_text=template_render_text(field_config, file_path),
    )


def template_fields(field_config: dict[str, object]) -> list[str]:
    raw_fields = field_config.get("fields")
    if not isinstance(raw_fields, list):
        return []

    fields: list[str] = []
    seen: set[str] = set()
    for raw_field in raw_fields:
        if not isinstance(raw_field, str):
            continue
        field = canonical_field_name(raw_field)
        if not field or field in seen:
            continue
        fields.append(field)
        seen.add(field)
    return fields


def template_file_path(template: Template) -> str | None:
    if template.file is None:
        return None

    candidates = _file_path_candidates(
        storage_path=template.file.storage_path,
        stored_name=template.file.stored_name,
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(candidates[0]) if candidates else None


def custom_template_fields(fields: list[str]) -> list[str]:
    custom_fields: list[str] = []
    for field in fields:
        custom_name = custom_field_name(field)
        if custom_name and custom_name not in custom_fields:
            custom_fields.append(custom_name)
    return custom_fields


def custom_field_name(field: str) -> str | None:
    field = canonical_field_name(field)
    if field.startswith("custom_fields."):
        name = field.removeprefix("custom_fields.").strip()
        return name or None
    if field not in STANDARD_TEMPLATE_FIELDS:
        return field
    return None


def template_render_text(field_config: dict[str, object], file_path: str | None) -> str | None:
    parse_data = field_config.get("parse")
    if isinstance(parse_data, dict):
        raw_content = parse_data.get("raw_content")
        if isinstance(raw_content, dict):
            template_text = raw_content.get("template_text")
            if isinstance(template_text, str) and template_text.strip():
                return template_text

    if not file_path:
        return None
    path = Path(file_path)
    if not path.exists():
        return None
    template_text = read_template_text(path)
    return template_text if template_text.strip() else None


def get_source_value(source_data: dict[str, object], field: str) -> object | None:
    field = canonical_field_name(field)
    direct_value = source_data.get(field)
    if _has_value(direct_value):
        return direct_value

    answers = source_data.get("answers")
    if isinstance(answers, dict):
        answer_value = _dict_value(answers, field)
        if _has_value(answer_value):
            return answer_value

    custom_fields = source_data.get("custom_fields")
    if isinstance(custom_fields, dict):
        custom_name = custom_field_name(field) or field.removeprefix("custom_fields.")
        custom_value = _dict_value(custom_fields, custom_name)
        if _has_value(custom_value):
            return custom_value

    if field.startswith("custom_fields."):
        return get_source_value(source_data, field.removeprefix("custom_fields."))
    return None


def _file_path_candidates(storage_path: str, stored_name: str) -> list[Path]:
    settings = get_settings()
    storage_root = Path(settings.storage_root)
    raw_path = Path(storage_path)

    candidates = [raw_path]
    if not raw_path.is_absolute():
        candidates.append(Path.cwd() / raw_path)
    candidates.extend(
        [
            storage_root / "uploads" / stored_name,
            storage_root / "templates" / stored_name,
            storage_root / stored_name,
        ]
    )

    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        unique_candidates.append(candidate)
        seen.add(key)
    return unique_candidates


def _dict_value(data: dict[Any, Any], key: str) -> object | None:
    value = data.get(key)
    if _has_value(value):
        return value
    if key.startswith("custom_fields."):
        value = data.get(key.removeprefix("custom_fields."))
        if _has_value(value):
            return value
    return None


def _has_value(value: object | None) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list | dict):
        return bool(value)
    return True

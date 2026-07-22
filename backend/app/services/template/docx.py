from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from app.schemas.report import TemplateParseResult
from app.services.template.base import TemplateService

PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\}\}")


class DocxTemplateService(TemplateService):
    async def parse_template(self, file_path: str) -> TemplateParseResult:
        template_path = Path(file_path)
        if template_path.suffix.lower() != ".docx":
            msg = "Only .docx template files are supported now."
            raise ValueError(msg)
        if not template_path.exists():
            msg = f"Template file not found: {file_path}"
            raise FileNotFoundError(msg)

        template_text = _read_docx_text(template_path)
        fields = _extract_placeholders(template_text)
        template_type = _guess_template_type(fields, template_path.name)

        return TemplateParseResult(
            template_type=template_type,
            fields=fields,
            description=f"Parsed {len(fields)} placeholder(s) from {template_path.name}",
            raw_content={
                "source": "docx",
                "path": str(template_path),
                "placeholder_count": len(fields),
            },
        )


def _read_docx_text(template_path: Path) -> str:
    try:
        with ZipFile(template_path) as docx:
            xml_names = [
                name
                for name in docx.namelist()
                if name == "word/document.xml"
                or name.startswith(("word/header", "word/footer"))
            ]
            return "\n".join(
                _extract_xml_text(docx.read(name).decode("utf-8")) for name in xml_names
            )
    except BadZipFile as exc:
        msg = f"Invalid docx template file: {template_path}"
        raise ValueError(msg) from exc


def _extract_xml_text(xml_text: str) -> str:
    root = ElementTree.fromstring(xml_text)
    text_parts = [
        element.text or ""
        for element in root.iter()
        if element.tag.endswith("}t") or element.tag == "t"
    ]
    return "".join(text_parts)


def _extract_placeholders(template_text: str) -> list[str]:
    fields = PLACEHOLDER_PATTERN.findall(template_text)
    return sorted(set(fields), key=fields.index)


def _guess_template_type(fields: list[str], file_name: str) -> str:
    lowered_name = file_name.lower()
    if "weekly" in lowered_name or "week" in lowered_name or "周报" in file_name:
        return "weekly"
    if "daily" in lowered_name or "day" in lowered_name or "日报" in file_name:
        return "daily"
    if "week_summary" in fields or "next_week_plan" in fields:
        return "weekly"
    return "daily"

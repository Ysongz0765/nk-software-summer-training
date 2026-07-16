from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.report import TemplateParseResult
from app.services.template.mock import MockTemplateService

router = APIRouter()
template_service = MockTemplateService()


@router.post("", response_model=ApiResponse[dict[str, object]])
async def create_template(payload: dict[str, object]) -> ApiResponse[dict[str, object]]:
    return ApiResponse(data={"template_id": 1, "payload": payload})


@router.get("", response_model=ApiResponse[list[dict[str, object]]])
async def list_templates() -> ApiResponse[list[dict[str, object]]]:
    return ApiResponse(data=[{"id": 1, "name": "Mock daily template", "template_type": "daily"}])


@router.get("/{template_id}", response_model=ApiResponse[dict[str, object]])
async def get_template(template_id: int) -> ApiResponse[dict[str, object]]:
    return ApiResponse(
        data={
            "id": template_id,
            "name": "Mock daily template",
            "template_type": "daily",
        }
    )


@router.post("/parse", response_model=ApiResponse[TemplateParseResult])
async def parse_template(payload: dict[str, str]) -> ApiResponse[TemplateParseResult]:
    result = await template_service.parse_template(payload["file_path"])
    return ApiResponse(data=result)

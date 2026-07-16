from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.common import ApiResponse
from app.schemas.report import OCRResult
from app.services.ocr.mock import MockOCRService

router = APIRouter()
ocr_service = MockOCRService()


class OCRRecognizeRequest(BaseModel):
    file_path: str


@router.post("/recognize", response_model=ApiResponse[OCRResult])
async def recognize(payload: OCRRecognizeRequest) -> ApiResponse[OCRResult]:
    result = await ocr_service.recognize(payload.file_path)
    return ApiResponse(data=result)

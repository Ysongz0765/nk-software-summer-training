from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.exceptions import AppError, UnsupportedFileTypeError
from app.schemas.common import ApiResponse
from app.schemas.report import OCRResult, TaskExtractionInput, TaskItem
from app.services.ai.base import AIReportService
from app.services.ai.factory import get_ai_report_service
from app.services.ocr.base import OCRService
from app.services.ocr.factory import get_ocr_service

router = APIRouter()
OCR_UPLOAD_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf"}


class OCRRecognizeRequest(BaseModel):
    file_path: str


class OCRBatchRecognizeRequest(BaseModel):
    file_paths: list[str] = Field(min_length=1, max_length=20)


class OCRBatchItemResult(BaseModel):
    file_path: str
    status: str
    result: OCRResult | None = None
    code: int | None = None
    message: str | None = None


class OCRUploadRecognizeResult(BaseModel):
    file_id: str
    original_name: str
    stored_name: str
    ocr: OCRResult


class OCRTaskExtractionRequest(BaseModel):
    file_path: str
    report_type: str = "daily"
    context: dict[str, object] = Field(default_factory=dict)


class OCRTaskExtractionResult(BaseModel):
    ocr: OCRResult
    tasks: list[TaskItem] = Field(default_factory=list)


@router.post("/recognize", response_model=ApiResponse[OCRResult])
async def recognize(
    payload: OCRRecognizeRequest,
    ocr_service: Annotated[OCRService, Depends(get_ocr_service)],
) -> ApiResponse[OCRResult]:
    result = await ocr_service.recognize(payload.file_path)
    return ApiResponse(data=result)


@router.post("/recognize-upload", response_model=ApiResponse[OCRUploadRecognizeResult])
async def recognize_upload(
    file: Annotated[UploadFile, File(...)],
    ocr_service: Annotated[OCRService, Depends(get_ocr_service)],
) -> ApiResponse[OCRUploadRecognizeResult]:
    stored_name = await _store_ocr_upload(file)
    result = await ocr_service.recognize(stored_name)
    return ApiResponse(
        data=OCRUploadRecognizeResult(
            file_id=stored_name,
            original_name=file.filename or stored_name,
            stored_name=stored_name,
            ocr=result,
        )
    )


@router.post("/recognize-batch", response_model=ApiResponse[list[OCRBatchItemResult]])
async def recognize_batch(
    payload: OCRBatchRecognizeRequest,
    ocr_service: Annotated[OCRService, Depends(get_ocr_service)],
) -> ApiResponse[list[OCRBatchItemResult]]:
    results: list[OCRBatchItemResult] = []
    for file_path in payload.file_paths:
        try:
            result = await ocr_service.recognize(file_path)
        except AppError as exc:
            results.append(
                OCRBatchItemResult(
                    file_path=file_path,
                    status="failed",
                    code=exc.code,
                    message=exc.message,
                )
            )
            continue

        results.append(
            OCRBatchItemResult(
                file_path=file_path,
                status="success",
                result=result,
            )
        )

    return ApiResponse(data=results)


@router.post("/extract-tasks", response_model=ApiResponse[OCRTaskExtractionResult])
async def extract_tasks_from_ocr(
    payload: OCRTaskExtractionRequest,
    ocr_service: Annotated[OCRService, Depends(get_ocr_service)],
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
) -> ApiResponse[OCRTaskExtractionResult]:
    ocr_result = await ocr_service.recognize(payload.file_path)
    tasks = await _extract_tasks_from_ocr_result(
        ocr_result=ocr_result,
        file_path=payload.file_path,
        report_type=payload.report_type,
        context=payload.context,
        ai_service=ai_service,
    )

    return ApiResponse(data=OCRTaskExtractionResult(ocr=ocr_result, tasks=tasks))


@router.post("/extract-tasks-upload", response_model=ApiResponse[OCRTaskExtractionResult])
async def extract_tasks_from_upload(
    file: Annotated[UploadFile, File(...)],
    ocr_service: Annotated[OCRService, Depends(get_ocr_service)],
    ai_service: Annotated[AIReportService, Depends(get_ai_report_service)],
    report_type: Annotated[str, Form()] = "daily",
) -> ApiResponse[OCRTaskExtractionResult]:
    stored_name = await _store_ocr_upload(file)
    ocr_result = await ocr_service.recognize(stored_name)
    tasks = await _extract_tasks_from_ocr_result(
        ocr_result=ocr_result,
        file_path=stored_name,
        report_type=report_type,
        context={"original_name": file.filename or stored_name},
        ai_service=ai_service,
    )
    return ApiResponse(data=OCRTaskExtractionResult(ocr=ocr_result, tasks=tasks))


async def _store_ocr_upload(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in OCR_UPLOAD_SUFFIXES:
        raise UnsupportedFileTypeError(
            "only png, jpg, jpeg and pdf files are supported for OCR upload"
        )

    settings = get_settings()
    storage_dir = Path(settings.storage_root) / "uploads"
    storage_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid4().hex}{suffix}"
    target = storage_dir / stored_name
    content = await file.read()
    if not content:
        raise UnsupportedFileTypeError("empty OCR upload file")

    target.write_bytes(content)
    return stored_name


async def _extract_tasks_from_ocr_result(
    ocr_result: OCRResult,
    file_path: str,
    report_type: str,
    context: dict[str, object],
    ai_service: AIReportService,
) -> list[TaskItem]:
    if not ocr_result.text.strip():
        return []

    extraction_context = {
        **context,
        "ocr_file_path": file_path,
        "ocr_confidence": ocr_result.confidence,
        "ocr_pages": ocr_result.pages,
    }
    return await ai_service.extract_tasks(
        TaskExtractionInput(
            source_text=ocr_result.text,
            report_type=report_type,
            context=extraction_context,
        )
    )

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.exceptions import OCRServiceUnavailableError
from app.services.ocr.base import OCRService
from app.services.ocr.mock import MockOCRService
from app.services.ocr.paddle import PaddleOCRService
from app.services.ocr.qwen import QwenVisionOCRService


@lru_cache
def _get_mock_ocr_service() -> MockOCRService:
    return MockOCRService()


def create_ocr_service(settings: Settings) -> OCRService:
    provider = settings.ocr_provider.strip().lower() or "mock"

    if provider == "mock":
        return _get_mock_ocr_service()
    if provider in {"paddle", "paddleocr"}:
        return PaddleOCRService(storage_root=settings.storage_root)
    if provider in {"qwen", "qwen-vl", "qwen_vl", "dashscope"}:
        api_key = (settings.qwen_api_key or settings.ai_api_key or "").strip()
        if not api_key:
            raise OCRServiceUnavailableError(
                "QWEN_API_KEY is required when OCR_PROVIDER=qwen"
            )
        return QwenVisionOCRService(
            api_key=api_key,
            storage_root=settings.storage_root,
            base_url=settings.qwen_base_url,
            model=settings.qwen_vision_model,
            timeout_seconds=settings.qwen_timeout_seconds,
        )

    raise OCRServiceUnavailableError(
        f"unsupported OCR_PROVIDER '{provider}', supported providers: mock, paddle, qwen"
    )


def get_ocr_service() -> OCRService:
    return create_ocr_service(get_settings())

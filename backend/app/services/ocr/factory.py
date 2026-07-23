from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.exceptions import OCRServiceUnavailableError
from app.services.ocr.base import OCRService
from app.services.ocr.mock import MockOCRService
from app.services.ocr.paddle import PaddleOCRService


@lru_cache
def _get_mock_ocr_service() -> MockOCRService:
    return MockOCRService()


def create_ocr_service(settings: Settings) -> OCRService:
    provider = settings.ocr_provider.strip().lower() or "mock"

    if provider == "mock":
        return _get_mock_ocr_service()
    if provider in {"paddle", "paddleocr"}:
        return PaddleOCRService(storage_root=settings.storage_root)

    raise OCRServiceUnavailableError(
        f"unsupported OCR_PROVIDER '{provider}', supported providers: mock, paddle"
    )


def get_ocr_service() -> OCRService:
    return create_ocr_service(get_settings())

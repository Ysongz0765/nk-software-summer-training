from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.exceptions import AIServiceUnavailableError, OCRServiceUnavailableError
from app.services.ai.deepseek import DeepSeekAIReportService
from app.services.ai.factory import create_ai_report_service
from app.services.ai.mock import MockAIReportService
from app.services.ocr.factory import create_ocr_service
from app.services.ocr.mock import MockOCRService
from app.services.ocr.paddle import PaddleOCRService


def test_ai_factory_returns_mock_provider() -> None:
    service = create_ai_report_service(Settings(ai_provider=" MOCK "))

    assert isinstance(service, MockAIReportService)


def test_ai_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(AIServiceUnavailableError):
        create_ai_report_service(Settings(ai_provider="openai"))


def test_ai_factory_returns_deepseek_provider() -> None:
    service = create_ai_report_service(
        Settings(
            ai_provider="deepseek",
            ai_api_key="sk-placeholder",
            ai_model="deepseek-v4-flash",
        )
    )

    assert isinstance(service, DeepSeekAIReportService)


def test_ai_factory_rejects_deepseek_without_api_key() -> None:
    with pytest.raises(AIServiceUnavailableError):
        create_ai_report_service(Settings(ai_provider="deepseek", ai_api_key=""))


def test_ocr_factory_returns_mock_provider() -> None:
    service = create_ocr_service(Settings(ocr_provider=" Mock "))

    assert isinstance(service, MockOCRService)


def test_ocr_factory_returns_paddle_provider() -> None:
    service = create_ocr_service(Settings(ocr_provider="paddle"))

    assert isinstance(service, PaddleOCRService)


def test_ocr_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(OCRServiceUnavailableError):
        create_ocr_service(Settings(ocr_provider="cloud"))

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.core.exceptions import AIServiceUnavailableError
from app.services.ai.base import AIReportService
from app.services.ai.deepseek import (
    DEEPSEEK_DEFAULT_BASE_URL,
    DEEPSEEK_DEFAULT_MODEL,
    DeepSeekAIReportService,
)
from app.services.ai.mock import MockAIReportService


@lru_cache
def _get_mock_ai_report_service() -> MockAIReportService:
    return MockAIReportService()


def create_ai_report_service(settings: Settings) -> AIReportService:
    provider = settings.ai_provider.strip().lower() or "mock"

    if provider == "mock":
        return _get_mock_ai_report_service()
    if provider == "deepseek":
        api_key = settings.ai_api_key or ""
        base_url = settings.ai_base_url or DEEPSEEK_DEFAULT_BASE_URL
        model = (
            DEEPSEEK_DEFAULT_MODEL
            if settings.ai_model.strip() == "mock-reportflow"
            else settings.ai_model
        )
        return DeepSeekAIReportService(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=settings.ai_timeout_seconds,
        )

    raise AIServiceUnavailableError(
        f"unsupported AI_PROVIDER '{provider}', supported providers: mock, deepseek"
    )


def get_ai_report_service() -> AIReportService:
    return create_ai_report_service(get_settings())

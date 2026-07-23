from __future__ import annotations

import asyncio

from app.services.ocr.mock import MockOCRService


def test_mock_ocr_service_returns_file_specific_text() -> None:
    async def run() -> None:
        service = MockOCRService()
        result = await service.recognize("uploads/daily-report.pdf")

        assert result.pages == 2
        assert result.language == "zh"
        assert "daily-report.pdf" in result.text
        assert "完成 OCR 模块接口联调" in result.text

    asyncio.run(run())

from __future__ import annotations

from app.schemas.report import OCRResult
from app.services.ocr.base import OCRService


class MockOCRService(OCRService):
    async def recognize(self, file_path: str) -> OCRResult:
        return OCRResult(
            text=f"Mock OCR text extracted from {file_path}",
            pages=1,
            confidence=0.98,
            language="zh",
        )

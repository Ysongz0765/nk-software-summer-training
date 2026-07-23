from __future__ import annotations

from pathlib import Path

from app.schemas.report import OCRResult
from app.services.ocr.base import OCRService


class MockOCRService(OCRService):
    async def recognize(self, file_path: str) -> OCRResult:
        file_name = Path(file_path).name or "unknown"
        suffix = Path(file_name).suffix.lower()
        pages = 2 if suffix == ".pdf" else 1
        confidence = 0.92 if suffix == ".pdf" else 0.96

        return OCRResult(
            text=(
                f"Mock OCR text extracted from {file_name}\n"
                "完成 OCR 模块接口联调\n"
                "正在整理任务提取规则\n"
                "计划补充真实服务接入配置"
            ),
            pages=pages,
            confidence=confidence,
            language="zh",
        )

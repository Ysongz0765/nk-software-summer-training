from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.report import OCRResult


class OCRService(ABC):
    @abstractmethod
    async def recognize(self, file_path: str) -> OCRResult:
        raise NotImplementedError

from app.services.ocr.base import OCRService
from app.services.ocr.factory import create_ocr_service, get_ocr_service
from app.services.ocr.mock import MockOCRService
from app.services.ocr.paddle import PaddleOCRService

__all__ = [
    "MockOCRService",
    "OCRService",
    "PaddleOCRService",
    "create_ocr_service",
    "get_ocr_service",
]

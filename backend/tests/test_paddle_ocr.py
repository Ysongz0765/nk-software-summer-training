from __future__ import annotations

import asyncio

import pytest

from app.core.exceptions import ResourceNotFoundError, UnsupportedFileTypeError
from app.services.ocr.paddle import PaddleOCRService


class FakePaddleEngine:
    def predict(self, input: str) -> list[dict[str, object]]:
        if input.endswith("page-1.png"):
            return [{"rec_texts": ["第一页完成接口设计"], "rec_scores": [0.9]}]
        if input.endswith("page-2.png"):
            return [{"rec_texts": ["第二页正在联调识别"], "rec_scores": [0.7]}]
        return [
            {
                "input_path": input,
                "rec_texts": ["完成 PaddleOCR 接入", "正在联调图片识别"],
                "rec_scores": [0.9, 0.8],
            }
        ]


def test_paddle_ocr_service_builds_ocr_result_from_engine_output(tmp_path) -> None:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    image_path = uploads_dir / "daily.png"
    image_path.write_bytes(b"fake image bytes")

    async def run() -> None:
        service = PaddleOCRService(storage_root=str(tmp_path), engine=FakePaddleEngine())
        result = await service.recognize("daily.png")

        assert result.text == "完成 PaddleOCR 接入\n正在联调图片识别"
        assert result.pages == 1
        assert result.confidence == 0.85
        assert result.language == "zh"

    asyncio.run(run())


def test_paddle_ocr_service_accepts_storage_prefixed_path(tmp_path) -> None:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    image_path = uploads_dir / "daily.png"
    image_path.write_bytes(b"fake image bytes")

    async def run() -> None:
        service = PaddleOCRService(storage_root=str(tmp_path), engine=FakePaddleEngine())
        result = await service.recognize("storage/uploads/daily.png")

        assert "完成 PaddleOCR 接入" in result.text

    asyncio.run(run())


def test_paddle_ocr_service_recognizes_pdf_pages(tmp_path) -> None:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    pdf_path = uploads_dir / "daily.pdf"
    pdf_path.write_bytes(b"fake pdf bytes")

    def fake_pdf_renderer(pdf_source, output_dir, dpi):
        assert pdf_source == pdf_path
        assert dpi == 200
        page_1 = output_dir / "page-1.png"
        page_2 = output_dir / "page-2.png"
        page_1.write_bytes(b"fake page 1")
        page_2.write_bytes(b"fake page 2")
        return [page_1, page_2]

    async def run() -> None:
        service = PaddleOCRService(
            storage_root=str(tmp_path),
            engine=FakePaddleEngine(),
            pdf_renderer=fake_pdf_renderer,
        )
        result = await service.recognize("daily.pdf")

        assert result.pages == 2
        assert result.confidence == 0.8
        assert "--- Page 1 ---" in result.text
        assert "第一页完成接口设计" in result.text
        assert "--- Page 2 ---" in result.text
        assert "第二页正在联调识别" in result.text

    asyncio.run(run())


def test_paddle_ocr_service_rejects_unsupported_file_type(tmp_path) -> None:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    text_path = uploads_dir / "daily.txt"
    text_path.write_text("not an OCR source", encoding="utf-8")

    async def run() -> None:
        service = PaddleOCRService(storage_root=str(tmp_path), engine=FakePaddleEngine())

        with pytest.raises(UnsupportedFileTypeError):
            await service.recognize("daily.txt")

    asyncio.run(run())


def test_paddle_ocr_service_rejects_missing_file(tmp_path) -> None:
    async def run() -> None:
        service = PaddleOCRService(storage_root=str(tmp_path), engine=FakePaddleEngine())

        with pytest.raises(ResourceNotFoundError):
            await service.recognize("missing.png")

    asyncio.run(run())

from __future__ import annotations

import asyncio
import importlib
import os
import tempfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import cast

from app.core.config import get_settings
from app.core.exceptions import (
    AppError,
    OCRServiceUnavailableError,
    ResourceNotFoundError,
    UnsupportedFileTypeError,
)
from app.schemas.report import OCRResult
from app.services.ocr.base import OCRService

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
SUPPORTED_PADDLE_SUFFIXES = SUPPORTED_IMAGE_SUFFIXES | {".pdf"}
DEFAULT_PDF_DPI = 200
PdfRenderer = Callable[[Path, Path, int], list[Path]]


class PaddleOCRService(OCRService):
    def __init__(
        self,
        storage_root: str | None = None,
        language: str = "ch",
        engine: object | None = None,
        pdf_renderer: PdfRenderer | None = None,
        pdf_dpi: int = DEFAULT_PDF_DPI,
    ) -> None:
        self._storage_root = storage_root
        self._language = language
        self._engine = engine
        self._pdf_renderer = pdf_renderer or _render_pdf_pages
        self._pdf_dpi = pdf_dpi

    async def recognize(self, file_path: str) -> OCRResult:
        try:
            source_path = _resolve_source_path(file_path, self._storage_root)
            engine = self._engine or _get_paddle_engine(self._language)

            if source_path.suffix.lower() == ".pdf":
                return await self._recognize_pdf(source_path, engine)

            return await self._recognize_image(source_path, engine)
        except AppError:
            raise
        except Exception as exc:
            raise OCRServiceUnavailableError("PaddleOCR service failed") from exc

    async def _recognize_pdf(self, pdf_path: Path, engine: object) -> OCRResult:
        with tempfile.TemporaryDirectory(prefix="reportflow-ocr-") as temp_dir:
            page_image_paths = await asyncio.to_thread(
                self._pdf_renderer,
                pdf_path,
                Path(temp_dir),
                self._pdf_dpi,
            )
            if not page_image_paths:
                return OCRResult(text="", pages=0, confidence=0.0, language="zh")

            page_results = [
                await self._recognize_image(page_image_path, engine)
                for page_image_path in page_image_paths
            ]

        return OCRResult(
            text=_format_pdf_text(page_results),
            pages=len(page_results),
            confidence=_average_score([result.confidence for result in page_results]),
            language="zh",
        )

    async def _recognize_image(self, image_path: Path, engine: object) -> OCRResult:
        try:
            raw_result = await asyncio.to_thread(_predict, engine, image_path)
        except OCRServiceUnavailableError:
            raise
        except Exception as exc:
            raise OCRServiceUnavailableError("PaddleOCR recognition failed") from exc

        texts, scores = _extract_texts_and_scores(raw_result)
        return OCRResult(
            text="\n".join(texts),
            pages=1,
            confidence=_average_score(scores),
            language="zh",
        )


@lru_cache
def _get_paddle_engine(language: str) -> object:
    _configure_paddle_cache()
    try:
        paddleocr = importlib.import_module("paddleocr")
    except ImportError as exc:
        raise OCRServiceUnavailableError(
            "paddleocr is not installed; install backend with .[ocr]"
        ) from exc

    paddle_ocr_factory = getattr(paddleocr, "PaddleOCR", None)
    if not callable(paddle_ocr_factory):
        raise OCRServiceUnavailableError("paddleocr.PaddleOCR is unavailable")

    factory = cast(Callable[..., object], paddle_ocr_factory)
    try:
        return factory(
            lang=language,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
    except TypeError:
        try:
            return factory(lang=language, use_angle_cls=True)
        except Exception as exc:
            raise OCRServiceUnavailableError("PaddleOCR engine initialization failed") from exc
    except Exception as exc:
        raise OCRServiceUnavailableError("PaddleOCR engine initialization failed") from exc


def _resolve_source_path(file_path: str, storage_root: str | None) -> Path:
    if not file_path.strip():
        raise ResourceNotFoundError("file_path is required")

    settings = get_settings()
    storage_path = Path(storage_root or settings.storage_root).resolve()
    raw_path = Path(file_path)
    candidates = _candidate_paths(raw_path, storage_path)

    for candidate in candidates:
        resolved = candidate.resolve()
        if not _is_relative_to(resolved, storage_path):
            continue
        if resolved.suffix.lower() not in SUPPORTED_PADDLE_SUFFIXES:
            raise UnsupportedFileTypeError(
                "only png, jpg, jpeg and pdf files are supported for OCR"
            )
        if resolved.exists():
            return resolved

    raise ResourceNotFoundError(f"OCR source file not found: {file_path}")


def _candidate_paths(raw_path: Path, storage_path: Path) -> list[Path]:
    if raw_path.is_absolute():
        return [raw_path]
    if len(raw_path.parts) == 1:
        return [storage_path / "uploads" / raw_path, storage_path / raw_path]

    candidates: list[Path] = []
    normalized_path = _strip_storage_prefix(raw_path, storage_path)
    if normalized_path != raw_path:
        candidates.append(storage_path / normalized_path)
    candidates.append(storage_path / raw_path)
    return candidates


def _strip_storage_prefix(raw_path: Path, storage_path: Path) -> Path:
    parts = raw_path.parts
    storage_prefixes = {storage_path.name.lower(), "storage"}
    if parts and parts[0].lower() in storage_prefixes:
        return Path(*parts[1:])
    return raw_path


def _configure_paddle_cache() -> None:
    settings = get_settings()
    cache_root = (Path(settings.storage_root) / "cache").resolve()
    paddle_home = cache_root / "paddle"
    paddlex_home = cache_root / ".paddlex"
    paddle_home.mkdir(parents=True, exist_ok=True)
    paddlex_home.mkdir(parents=True, exist_ok=True)

    os.environ["HOME"] = str(cache_root)
    os.environ["USERPROFILE"] = str(cache_root)
    os.environ["XDG_CACHE_HOME"] = str(cache_root)
    os.environ["PADDLE_HOME"] = str(paddle_home)
    os.environ["PADDLE_PDX_CACHE_HOME"] = str(paddlex_home)
    os.environ["PADDLE_PDX_MODEL_SOURCE"] = os.environ.get("PADDLE_PDX_MODEL_SOURCE", "BOS")
    os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = os.environ.get(
        "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK",
        "True",
    )
    os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = os.environ.get(
        "PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT",
        "False",
    )
    os.environ["FLAGS_use_mkldnn"] = os.environ.get("FLAGS_use_mkldnn", "0")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _predict(engine: object, image_path: Path) -> object:
    predict = getattr(engine, "predict", None)
    if callable(predict):
        try:
            return predict(input=str(image_path))
        except TypeError:
            return predict(str(image_path))

    legacy_ocr = getattr(engine, "ocr", None)
    if callable(legacy_ocr):
        try:
            return legacy_ocr(str(image_path), cls=True)
        except TypeError:
            return legacy_ocr(str(image_path))

    raise OCRServiceUnavailableError("PaddleOCR engine has no predict or ocr method")


def _render_pdf_pages(pdf_path: Path, output_dir: Path, dpi: int) -> list[Path]:
    pymupdf = _import_pymupdf()
    open_document = getattr(pymupdf, "open", None)
    if not callable(open_document):
        raise OCRServiceUnavailableError("PyMuPDF open function is unavailable")

    document = cast(Callable[[str], object], open_document)(str(pdf_path))
    page_paths: list[Path] = []
    try:
        for page_index, page in enumerate(cast(Iterable[object], document), start=1):
            get_pixmap = getattr(page, "get_pixmap", None)
            if not callable(get_pixmap):
                raise OCRServiceUnavailableError("PyMuPDF page get_pixmap is unavailable")

            pixmap = _create_pixmap(cast(Callable[..., object], get_pixmap), dpi)
            save = getattr(pixmap, "save", None)
            if not callable(save):
                raise OCRServiceUnavailableError("PyMuPDF pixmap save is unavailable")

            page_path = output_dir / f"page-{page_index}.png"
            cast(Callable[[str], object], save)(str(page_path))
            page_paths.append(page_path)
    finally:
        close_document = getattr(document, "close", None)
        if callable(close_document):
            close_document()

    return page_paths


def _import_pymupdf() -> object:
    try:
        return importlib.import_module("pymupdf")
    except ImportError:
        try:
            return importlib.import_module("fitz")
        except ImportError as exc:
            raise OCRServiceUnavailableError(
                "PyMuPDF is not installed; install backend with .[ocr]"
            ) from exc


def _create_pixmap(get_pixmap: Callable[..., object], dpi: int) -> object:
    try:
        return get_pixmap(dpi=dpi, alpha=False)
    except TypeError:
        return get_pixmap()


def _extract_texts_and_scores(raw_result: object) -> tuple[list[str], list[float]]:
    texts: list[str] = []
    scores: list[float] = []
    _collect_result(raw_result, texts, scores)
    return texts, scores


def _collect_result(value: object, texts: list[str], scores: list[float]) -> None:
    if isinstance(value, Mapping):
        _collect_mapping(value, texts, scores)
        return

    result_data = getattr(value, "res", None)
    if isinstance(result_data, Mapping):
        _collect_mapping(result_data, texts, scores)
        return

    if isinstance(value, Sequence) and not isinstance(value, str):
        _collect_sequence(value, texts, scores)


def _collect_mapping(value: Mapping[object, object], texts: list[str], scores: list[float]) -> None:
    rec_texts = value.get("rec_texts")
    rec_scores = value.get("rec_scores")
    if isinstance(rec_texts, Sequence) and not isinstance(rec_texts, str):
        score_values = (
            list(rec_scores)
            if isinstance(rec_scores, Sequence) and not isinstance(rec_scores, str)
            else []
        )
        for index, text in enumerate(rec_texts):
            score = score_values[index] if index < len(score_values) else None
            _append_text_score(text, score, texts, scores)
        return

    text = value.get("text") or value.get("rec_text")
    score = value.get("score") or value.get("confidence") or value.get("rec_score")
    _append_text_score(text, score, texts, scores)


def _collect_sequence(value: Sequence[object], texts: list[str], scores: list[float]) -> None:
    if len(value) >= 2 and isinstance(value[0], str):
        _append_text_score(value[0], value[1], texts, scores)
        return

    if len(value) >= 2 and isinstance(value[1], Sequence) and not isinstance(value[1], str):
        nested = value[1]
        if nested and isinstance(nested[0], str):
            score = nested[1] if len(nested) > 1 else None
            _append_text_score(nested[0], score, texts, scores)
            return

    for item in value:
        _collect_result(item, texts, scores)


def _append_text_score(
    raw_text: object,
    raw_score: object,
    texts: list[str],
    scores: list[float],
) -> None:
    if not isinstance(raw_text, str):
        return

    text = raw_text.strip()
    if not text:
        return

    texts.append(text)
    score = _coerce_score(raw_score)
    if score is not None:
        scores.append(score)


def _coerce_score(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return max(0.0, min(float(value), 1.0))
    return None


def _average_score(scores: list[float]) -> float:
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 4)


def _format_pdf_text(page_results: list[OCRResult]) -> str:
    parts: list[str] = []
    for page_number, result in enumerate(page_results, start=1):
        page_text = result.text.strip()
        if page_text:
            parts.append(f"--- Page {page_number} ---\n{page_text}")
        else:
            parts.append(f"--- Page {page_number} ---")
    return "\n\n".join(parts)

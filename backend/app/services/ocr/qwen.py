from __future__ import annotations

import asyncio
import base64
import mimetypes
import tempfile
from pathlib import Path
from typing import Any

import httpx

from app.core.exceptions import AppError, OCRServiceUnavailableError
from app.schemas.report import OCRResult
from app.services.ocr.base import OCRService
from app.services.ocr.paddle import (
    DEFAULT_PDF_DPI,
    _render_pdf_pages,
    _resolve_source_path,
)

DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_QWEN_VISION_MODEL = "qwen3-vl-plus"
DEFAULT_PROMPT = "\n".join(
    [
        "你是 ReportFlow 的工作内容截图识别助手。"
        "请从截图中提取可用于日报、周报或项目汇报的工作内容。",
        "",
        "请重点识别微信聊天记录、Git/GitHub/GitLab/IDE 截图、终端输出、"
        "代码评审和任务看板中的信息：",
        "- 完成了什么、正在做什么、下一步计划、阻塞或风险。",
        "- 需求、Bug、提交、分支、PR、Issue、文件名、命令、错误信息和测试结果。",
        "- 微信聊天请尽量保留发言人、时间、任务指派、进展反馈和交付物。",
        "- Git 类截图请尽量保留 commit hash、分支、变更摘要、冲突状态和 CI/测试状态。",
        "",
        "输出中文纯文本，不要输出 Markdown 表格，不要编造看不见的信息。"
        "若只能做普通 OCR，请完整转写可见文字。",
    ]
)


class QwenVisionOCRService(OCRService):
    def __init__(
        self,
        *,
        api_key: str,
        storage_root: str | None = None,
        base_url: str = DEFAULT_QWEN_BASE_URL,
        model: str = DEFAULT_QWEN_VISION_MODEL,
        timeout_seconds: float = 60.0,
        prompt: str = DEFAULT_PROMPT,
        pdf_dpi: int = DEFAULT_PDF_DPI,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._storage_root = storage_root
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._prompt = prompt
        self._pdf_dpi = pdf_dpi
        self._client = client

    async def recognize(self, file_path: str) -> OCRResult:
        try:
            source_path = _resolve_source_path(file_path, self._storage_root)

            if source_path.suffix.lower() == ".pdf":
                return await self._recognize_pdf(source_path)

            return await self._recognize_images([source_path])
        except AppError:
            raise
        except Exception as exc:
            raise OCRServiceUnavailableError("Qwen vision OCR service failed") from exc

    async def _recognize_pdf(self, pdf_path: Path) -> OCRResult:
        with tempfile.TemporaryDirectory(prefix="reportflow-qwen-ocr-") as temp_dir:
            page_image_paths = await asyncio.to_thread(
                _render_pdf_pages,
                pdf_path,
                Path(temp_dir),
                self._pdf_dpi,
            )
            if not page_image_paths:
                return OCRResult(text="", pages=0, confidence=0.0, language="zh")

            page_results = [
                await self._recognize_images([page_path])
                for page_path in page_image_paths
            ]

        return OCRResult(
            text=_format_pdf_text(page_results),
            pages=len(page_results),
            confidence=_average_score([result.confidence for result in page_results]),
            language="zh",
        )

    async def _recognize_images(self, image_paths: list[Path]) -> OCRResult:
        payload = self._build_payload(image_paths)
        response_data = await self._post_chat_completions(payload)
        text = _extract_message_text(response_data)

        return OCRResult(
            text=text,
            pages=len(image_paths),
            confidence=0.9 if text.strip() else 0.0,
            language="zh",
        )

    def _build_payload(self, image_paths: list[Path]) -> dict[str, Any]:
        content: list[dict[str, Any]] = [
            {"type": "text", "text": self._prompt},
        ]
        for index, image_path in enumerate(image_paths, start=1):
            if len(image_paths) > 1:
                content.append({"type": "text", "text": f"第 {index} 张截图："})
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _image_to_data_url(image_path)},
                }
            )

        return {
            "model": self._model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.1,
        }

    async def _post_chat_completions(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        if self._client is not None:
            return await _request_chat_completions(self._client, self._base_url, headers, payload)

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            return await _request_chat_completions(client, self._base_url, headers, payload)


async def _request_chat_completions(
    client: httpx.AsyncClient,
    base_url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        response = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise OCRServiceUnavailableError("Qwen vision OCR request failed") from exc

    if response.status_code >= 400:
        message = _extract_error_message(response)
        raise OCRServiceUnavailableError(f"Qwen vision OCR request failed: {message}")

    try:
        data = response.json()
    except ValueError as exc:
        raise OCRServiceUnavailableError("Qwen vision OCR returned invalid JSON") from exc

    if not isinstance(data, dict):
        raise OCRServiceUnavailableError("Qwen vision OCR returned unexpected response")
    return data


def _image_to_data_url(image_path: Path) -> str:
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _extract_message_text(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OCRServiceUnavailableError("Qwen vision OCR returned no choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise OCRServiceUnavailableError("Qwen vision OCR returned invalid choice")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise OCRServiceUnavailableError("Qwen vision OCR returned invalid message")

    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()

    raise OCRServiceUnavailableError("Qwen vision OCR returned empty content")


def _extract_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text[:300] or f"HTTP {response.status_code}"

    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        if isinstance(data.get("message"), str):
            return data["message"]

    return f"HTTP {response.status_code}"


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

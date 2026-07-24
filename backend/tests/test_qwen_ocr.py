from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.services.ocr.qwen import QwenVisionOCRService


class FakeQwenClient:
    def __init__(self) -> None:
        self.request: dict[str, Any] | None = None

    async def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any],
    ) -> httpx.Response:
        self.request = {"url": url, "headers": headers, "json": json}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "已完成：修复日报导出接口\n"
                                "正在做：联调微信截图识别\n"
                                "阻塞：无"
                            )
                        }
                    }
                ]
            },
        )


def test_qwen_ocr_service_calls_chat_completions_with_image_data_url(tmp_path) -> None:
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir()
    image_path = uploads_dir / "daily.png"
    image_path.write_bytes(b"fake image bytes")
    fake_client = FakeQwenClient()

    async def run() -> None:
        service = QwenVisionOCRService(
            api_key="sk-placeholder",
            storage_root=str(tmp_path),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen3-vl-plus",
            client=fake_client,  # type: ignore[arg-type]
        )
        result = await service.recognize("daily.png")

        assert result.text.startswith("已完成：修复日报导出接口")
        assert result.pages == 1
        assert result.confidence == 0.9
        assert result.language == "zh"

    asyncio.run(run())

    assert fake_client.request is not None
    assert fake_client.request["url"].endswith("/chat/completions")
    assert fake_client.request["headers"]["Authorization"] == "Bearer sk-placeholder"
    payload = fake_client.request["json"]
    assert payload["model"] == "qwen3-vl-plus"
    content = payload["messages"][0]["content"]
    image_items = [item for item in content if item["type"] == "image_url"]
    assert image_items[0]["image_url"]["url"].startswith("data:image/png;base64,")

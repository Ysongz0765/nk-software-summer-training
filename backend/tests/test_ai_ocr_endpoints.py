from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_ai_and_ocr_endpoints_use_mock_provider(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("OCR_PROVIDER", "mock")
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        ocr_response = client.post("/api/v1/ocr/recognize", json={"file_path": "uploads/daily.png"})
        extract_response = client.post(
            "/api/v1/ai/extract-tasks",
            json={"source_text": "完成 OCR 接口联调\n正在整理任务提取规则"},
        )
        report_response = client.post(
            "/api/v1/ai/generate-report",
            json={
                "report_type": "daily",
                "title": "日报",
                "report_date": "2026-07-23",
                "tasks": extract_response.json()["data"],
            },
        )
    finally:
        get_settings.cache_clear()

    assert ocr_response.status_code == 200
    assert "daily.png" in ocr_response.json()["data"]["text"]
    assert extract_response.status_code == 200
    assert extract_response.json()["data"][0]["title"] == "完成 OCR 接口联调"
    assert report_response.status_code == 200
    assert (
        report_response.json()["data"]["summary"]
        == "本期共识别 2 项任务，已完成 1 项，推进中 1 项。"
    )


def test_ai_endpoint_returns_unified_error_for_unsupported_provider(monkeypatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "unsupported")
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.post("/api/v1/ai/extract-tasks", json={"source_text": "完成测试"})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 503
    assert response.json()["code"] == 50301


def test_ocr_endpoint_returns_unified_error_for_unsupported_provider(monkeypatch) -> None:
    monkeypatch.setenv("OCR_PROVIDER", "unsupported")
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.post("/api/v1/ocr/recognize", json={"file_path": "uploads/daily.png"})
    finally:
        get_settings.cache_clear()

    assert response.status_code == 503
    assert response.json()["code"] == 50302

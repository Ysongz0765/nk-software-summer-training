from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_ocr_recognize_upload_stores_file_and_returns_result(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OCR_PROVIDER", "mock")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/ocr/recognize-upload",
            files={"file": ("daily.png", b"fake image bytes", "image/png")},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["original_name"] == "daily.png"
    assert payload["stored_name"].endswith(".png")
    assert (tmp_path / "uploads" / payload["stored_name"]).exists()
    assert payload["ocr"]["language"] == "zh"
    assert payload["stored_name"] in payload["ocr"]["text"]


def test_ocr_recognize_upload_rejects_unsupported_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OCR_PROVIDER", "mock")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/ocr/recognize-upload",
            files={"file": ("daily.txt", b"fake text bytes", "text/plain")},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 415
    assert response.json()["code"] == 41500


def test_ocr_recognize_batch_returns_per_file_results(monkeypatch) -> None:
    monkeypatch.setenv("OCR_PROVIDER", "mock")
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/ocr/recognize-batch",
            json={"file_paths": ["uploads/daily.png", "uploads/weekly.jpg"]},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()["data"]
    assert [item["status"] for item in payload] == ["success", "success"]
    assert "daily.png" in payload[0]["result"]["text"]
    assert "weekly.jpg" in payload[1]["result"]["text"]


def test_ocr_extract_tasks_runs_ocr_then_ai(monkeypatch) -> None:
    monkeypatch.setenv("OCR_PROVIDER", "mock")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/ocr/extract-tasks",
            json={"file_path": "uploads/daily.png", "report_type": "daily"},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()["data"]
    assert "完成 OCR 模块接口联调" in payload["ocr"]["text"]
    assert payload["tasks"][0]["title"].startswith("Mock OCR text extracted")
    assert any(task["title"] == "完成 OCR 模块接口联调" for task in payload["tasks"])


def test_ocr_extract_tasks_upload_runs_full_flow(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OCR_PROVIDER", "mock")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/ocr/extract-tasks-upload",
            data={"report_type": "daily"},
            files={"file": ("daily.png", b"fake image bytes", "image/png")},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()["data"]
    assert "完成 OCR 模块接口联调" in payload["ocr"]["text"]
    assert any(task["title"] == "完成 OCR 模块接口联调" for task in payload["tasks"])


def test_ocr_recognize_upload_accepts_pdf(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OCR_PROVIDER", "mock")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()

    try:
        client = TestClient(app)
        response = client.post(
            "/api/v1/ocr/recognize-upload",
            files={"file": ("daily.pdf", b"fake pdf bytes", "application/pdf")},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["stored_name"].endswith(".pdf")
    assert payload["ocr"]["pages"] == 2

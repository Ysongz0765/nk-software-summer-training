from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models as model_registry
from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import User


def test_project_crud_context_and_generation(monkeypatch, tmp_path) -> None:
    assert model_registry.Project.__tablename__ == "projects"
    client, session_factory = _build_client(monkeypatch, tmp_path)
    token = _register(session_factory, "alice")
    headers = _auth(token)

    project_response = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "ReportFlow AI",
            "description": "智能报表平台课程项目",
            "project_type": "课程项目",
            "current_stage": "功能联调",
            "start_date": "",
            "end_date": "",
            "tech_stack": ["FastAPI", "Vue", "MySQL"],
            "background_summary": "围绕 OCR、任务提取和报表生成建设演示平台。",
        },
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["data"]["id"]

    list_response = client.get("/api/v1/projects", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["name"] == "ReportFlow AI"

    patch_response = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"current_stage": "项目上下文联调"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["current_stage"] == "项目上下文联调"

    member_response = client.post(
        f"/api/v1/projects/{project_id}/members",
        headers=headers,
        json={"name": "小王", "role": "后端", "responsibility": "API 与数据库"},
    )
    assert member_response.status_code == 200

    task_response = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={
            "title": "接入项目上下文报表生成",
            "status": "in_progress",
            "module": "AI",
            "owner": "小王",
            "due_date": "",
        },
    )
    assert task_response.status_code == 200
    task_id = task_response.json()["data"]["id"]

    done_response = client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        headers=headers,
        json={"status": "completed"},
    )
    assert done_response.status_code == 200
    assert done_response.json()["data"]["completed_at"] is not None

    upload_response = client.post(
        "/api/v1/files/upload",
        headers=headers,
        data={"project_id": str(project_id)},
        files={"file": ("daily.txt", b"completed project context tests", "text/plain")},
    )
    assert upload_response.status_code == 200
    file_id = upload_response.json()["data"]["record_id"]
    assert upload_response.json()["data"]["project_id"] == project_id

    report_response = client.post(
        "/api/v1/reports",
        headers=headers,
        json={
            "project_id": project_id,
            "report_type": "daily",
            "title": "项目日报",
            "report_date": "2026-07-24",
            "source_data": {"summary": "完成项目空间接口联调。"},
        },
    )
    assert report_response.status_code == 200
    assert report_response.json()["data"]["project"]["name"] == "ReportFlow AI"

    filtered_reports = client.get(
        "/api/v1/reports",
        headers=headers,
        params={"project_id": project_id},
    )
    assert filtered_reports.status_code == 200
    assert filtered_reports.json()["data"][0]["project_id"] == project_id

    context_response = client.get(f"/api/v1/projects/{project_id}/context", headers=headers)
    assert context_response.status_code == 200
    context = context_response.json()["data"]
    assert context["background_summary"].startswith("围绕 OCR")
    assert context["recent_files"][0]["id"] == file_id
    assert context["recent_reports"][0]["title"] == "项目日报"
    assert context["completed_tasks"][0]["title"] == "接入项目上下文报表生成"

    generated_response = client.post(
        "/api/v1/ai/generate-report",
        headers=headers,
        json={
            "project_id": project_id,
            "report_type": "daily",
            "report_date": "2026-07-24",
            "task_ids": [task_id],
            "file_ids": [file_id],
            "user_notes": "重点验证项目上下文不串项目",
            "source_data": {},
        },
    )
    assert generated_response.status_code == 200
    generated = generated_response.json()["data"]
    assert "ReportFlow AI" in generated["title"]
    assert "项目「ReportFlow AI」" in generated["summary"]
    assert "项目上下文" in generated["completed_tasks"][0]["title"]

    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_project_permissions_and_data_isolation(monkeypatch, tmp_path) -> None:
    client, session_factory = _build_client(monkeypatch, tmp_path)
    alice = _register(session_factory, "alice")
    bob = _register(session_factory, "bob")
    alice_headers = _auth(alice)
    bob_headers = _auth(bob)

    project_response = client.post(
        "/api/v1/projects",
        headers=alice_headers,
        json={"name": "Alice Project", "current_stage": "开发"},
    )
    assert project_response.status_code == 200
    alice_project_id = project_response.json()["data"]["id"]

    other_project_response = client.post(
        "/api/v1/projects",
        headers=alice_headers,
        json={"name": "Second Project", "current_stage": "测试"},
    )
    other_project_id = other_project_response.json()["data"]["id"]

    client.post(
        f"/api/v1/projects/{alice_project_id}/tasks",
        headers=alice_headers,
        json={"title": "只属于第一个项目", "status": "pending"},
    )
    client.post(
        f"/api/v1/projects/{other_project_id}/tasks",
        headers=alice_headers,
        json={"title": "只属于第二个项目", "status": "pending"},
    )

    denied_project = client.get(f"/api/v1/projects/{alice_project_id}", headers=bob_headers)
    assert denied_project.status_code == 403

    denied_upload = client.post(
        "/api/v1/files/upload",
        headers=bob_headers,
        data={"project_id": str(alice_project_id)},
        files={"file": ("proof.txt", b"wrong project", "text/plain")},
    )
    assert denied_upload.status_code == 403

    denied_generation = client.post(
        "/api/v1/ai/generate-report",
        headers=bob_headers,
        json={"project_id": alice_project_id, "report_type": "daily"},
    )
    assert denied_generation.status_code == 403

    context_response = client.get(
        f"/api/v1/projects/{alice_project_id}/context",
        headers=alice_headers,
    )
    task_titles = [task["title"] for task in context_response.json()["data"]["recent_tasks"]]
    assert "只属于第一个项目" in task_titles
    assert "只属于第二个项目" not in task_titles

    app.dependency_overrides.clear()
    get_settings.cache_clear()


def _build_client(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), session_factory


def _register(session_factory, username: str) -> str:
    with session_factory() as session:
        user = User(
            username=username,
            email=f"{username}@example.com",
            hashed_password="test-only",
            is_active=True,
        )
        session.add(user)
        session.commit()
    return create_access_token(username)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

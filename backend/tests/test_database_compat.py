from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models as model_registry
from app.core.database import Base
from app.models import Report
from app.repositories.report import ReportRepository


def test_models_can_create_tables_and_persist_json_with_sqlite() -> None:
    assert model_registry.User.__tablename__ == "users"
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with session_factory() as session:
        repository = ReportRepository(session)
        report = repository.create(
            Report(
                report_type="daily",
                title="SQLite JSON check",
                report_date=date(2026, 7, 16),
                status="draft",
                content={"summary": "ok", "completed_tasks": [{"id": "task-1"}]},
                source_data={"raw": {"source": "test"}},
            )
        )
        stored = repository.get(report.id)

    assert stored is not None
    assert stored.content["summary"] == "ok"
    assert stored.source_data["raw"]["source"] == "test"


def test_mysql_database_url_can_be_parsed() -> None:
    from sqlalchemy.engine import make_url

    url = make_url("mysql+pymysql://reportflow:change_me@localhost:3306/reportflow?charset=utf8mb4")
    assert url.drivername == "mysql+pymysql"
    assert url.database == "reportflow"
    assert url.query["charset"] == "utf8mb4"


def test_postgresql_drivers_are_not_project_dependencies() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8").lower()
    assert "psycopg" not in pyproject
    assert "asyncpg" not in pyproject
    assert "pymysql" in pyproject

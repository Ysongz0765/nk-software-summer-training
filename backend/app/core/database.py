from __future__ import annotations

from collections.abc import Generator
from typing import Any

from sqlalchemy import JSON, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


JSONDict = JSON

settings = get_settings()
engine_kwargs: dict[str, Any] = {"echo": settings.debug, "future": True}
if settings.database_url and settings.database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif settings.database_url and settings.database_url.startswith("mysql"):
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 1800

engine = create_engine(settings.database_url or "sqlite+pysqlite:///:memory:", **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

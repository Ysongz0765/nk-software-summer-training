from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, JSONDict
from app.models.mixins import TimestampMixin


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    current_stage: Mapped[str | None] = mapped_column(String(128), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tech_stack: Mapped[list[str]] = mapped_column(JSONDict, default=list)
    background_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    user = relationship("User", back_populates="projects")
    tasks = relationship(
        "ProjectTask",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    members = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    memories = relationship(
        "ProjectMemory",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    files = relationship("UploadedFile", back_populates="project")
    reports = relationship("Report", back_populates="project")
    templates = relationship("Template", back_populates="project")
    exports = relationship("ExportRecord", back_populates="project")


class ProjectTask(TimestampMixin, Base):
    __tablename__ = "project_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    project = relationship("Project", back_populates="tasks")


class ProjectMember(TimestampMixin, Base):
    __tablename__ = "project_members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128))
    role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    responsibility: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="members")


class ProjectMemory(TimestampMixin, Base):
    __tablename__ = "project_memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(String(64), index=True)
    content: Mapped[str] = mapped_column(Text)
    source_ids: Mapped[list[int]] = mapped_column(JSONDict, default=list)
    is_user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    project = relationship("Project", back_populates="memories")

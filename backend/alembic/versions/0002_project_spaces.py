"""add project spaces

Revision ID: 0002_project_spaces
Revises: 0001_initial_schema
Create Date: 2026-07-24 14:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_project_spaces"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_type = sa.JSON()
mysql_table_kwargs = {
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
    "mysql_engine": "InnoDB",
}


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("project_type", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'active'")),
        sa.Column("current_stage", sa.String(length=128), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("tech_stack", json_type, nullable=False),
        sa.Column("background_summary", sa.Text(), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        **mysql_table_kwargs,
    )
    op.create_index("ix_projects_id", "projects", ["id"])
    op.create_index("ix_projects_user_id", "projects", ["user_id"])
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_last_activity_at", "projects", ["last_activity_at"])

    op.create_table(
        "project_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("module", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("priority", sa.String(length=32), nullable=True),
        sa.Column("owner", sa.String(length=128), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        **mysql_table_kwargs,
    )
    op.create_index("ix_project_tasks_id", "project_tasks", ["id"])
    op.create_index("ix_project_tasks_project_id", "project_tasks", ["project_id"])
    op.create_index("ix_project_tasks_status", "project_tasks", ["status"])

    op.create_table(
        "project_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("responsibility", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        **mysql_table_kwargs,
    )
    op.create_index("ix_project_members_id", "project_members", ["id"])
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])

    op.create_table(
        "project_memories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("memory_type", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_ids", json_type, nullable=False),
        sa.Column(
            "is_user_confirmed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        **mysql_table_kwargs,
    )
    op.create_index("ix_project_memories_id", "project_memories", ["id"])
    op.create_index("ix_project_memories_project_id", "project_memories", ["project_id"])
    op.create_index("ix_project_memories_memory_type", "project_memories", ["memory_type"])
    op.create_index(
        "ix_project_memories_is_user_confirmed",
        "project_memories",
        ["is_user_confirmed"],
    )

    _add_project_reference(
        table_name="uploaded_files",
        fk_name="fk_uploaded_files_project_id_projects",
    )
    _add_project_reference(
        table_name="templates",
        fk_name="fk_templates_project_id_projects",
    )
    _add_project_reference(
        table_name="reports",
        fk_name="fk_reports_project_id_projects",
    )
    _add_project_reference(
        table_name="export_records",
        fk_name="fk_export_records_project_id_projects",
    )


def downgrade() -> None:
    _drop_project_reference(
        table_name="export_records",
        fk_name="fk_export_records_project_id_projects",
    )
    _drop_project_reference(
        table_name="reports",
        fk_name="fk_reports_project_id_projects",
    )
    _drop_project_reference(
        table_name="templates",
        fk_name="fk_templates_project_id_projects",
    )
    _drop_project_reference(
        table_name="uploaded_files",
        fk_name="fk_uploaded_files_project_id_projects",
    )

    op.drop_index("ix_project_memories_is_user_confirmed", table_name="project_memories")
    op.drop_index("ix_project_memories_memory_type", table_name="project_memories")
    op.drop_index("ix_project_memories_project_id", table_name="project_memories")
    op.drop_index("ix_project_memories_id", table_name="project_memories")
    op.drop_table("project_memories")

    op.drop_index("ix_project_members_project_id", table_name="project_members")
    op.drop_index("ix_project_members_id", table_name="project_members")
    op.drop_table("project_members")

    op.drop_index("ix_project_tasks_status", table_name="project_tasks")
    op.drop_index("ix_project_tasks_project_id", table_name="project_tasks")
    op.drop_index("ix_project_tasks_id", table_name="project_tasks")
    op.drop_table("project_tasks")

    op.drop_index("ix_projects_last_activity_at", table_name="projects")
    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_index("ix_projects_user_id", table_name="projects")
    op.drop_index("ix_projects_id", table_name="projects")
    op.drop_table("projects")


def _add_project_reference(table_name: str, fk_name: str) -> None:
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.add_column(sa.Column("project_id", sa.Integer(), nullable=True))
        batch_op.create_index(f"ix_{table_name}_project_id", ["project_id"])
        batch_op.create_foreign_key(
            fk_name,
            "projects",
            ["project_id"],
            ["id"],
            ondelete="SET NULL",
        )


def _drop_project_reference(table_name: str, fk_name: str) -> None:
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.drop_constraint(fk_name, type_="foreignkey")
        batch_op.drop_index(f"ix_{table_name}_project_id")
        batch_op.drop_column("project_id")

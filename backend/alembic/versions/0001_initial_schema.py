"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-16 10:20:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
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
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        **mysql_table_kwargs,
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("stored_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'uploaded'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        **mysql_table_kwargs,
    )
    op.create_index("ix_uploaded_files_id", "uploaded_files", ["id"])
    op.create_index("ix_uploaded_files_user_id", "uploaded_files", ["user_id"])

    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_type", sa.String(length=32), nullable=False, server_default=sa.text("'daily'")),
        sa.Column("file_id", sa.Integer(), sa.ForeignKey("uploaded_files.id"), nullable=True),
        sa.Column("field_config", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        **mysql_table_kwargs,
    )
    op.create_index("ix_templates_id", "templates", ["id"])
    op.create_index("ix_templates_user_id", "templates", ["user_id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id"), nullable=True),
        sa.Column("report_type", sa.String(length=32), nullable=False, server_default=sa.text("'daily'")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("content", json_type, nullable=False),
        sa.Column("source_data", json_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        **mysql_table_kwargs,
    )
    op.create_index("ix_reports_id", "reports", ["id"])
    op.create_index("ix_reports_user_id", "reports", ["user_id"])

    op.create_table(
        "report_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content", json_type, nullable=False),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        **mysql_table_kwargs,
    )
    op.create_index("ix_report_versions_id", "report_versions", ["id"])
    op.create_index("ix_report_versions_report_id", "report_versions", ["report_id"])

    op.create_table(
        "export_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("reports.id"), nullable=False),
        sa.Column("export_type", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'created'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        **mysql_table_kwargs,
    )
    op.create_index("ix_export_records_id", "export_records", ["id"])
    op.create_index("ix_export_records_report_id", "export_records", ["report_id"])


def downgrade() -> None:
    op.drop_index("ix_export_records_report_id", table_name="export_records")
    op.drop_index("ix_export_records_id", table_name="export_records")
    op.drop_table("export_records")
    op.drop_index("ix_report_versions_report_id", table_name="report_versions")
    op.drop_index("ix_report_versions_id", table_name="report_versions")
    op.drop_table("report_versions")
    op.drop_index("ix_reports_user_id", table_name="reports")
    op.drop_index("ix_reports_id", table_name="reports")
    op.drop_table("reports")
    op.drop_index("ix_templates_user_id", table_name="templates")
    op.drop_index("ix_templates_id", table_name="templates")
    op.drop_table("templates")
    op.drop_index("ix_uploaded_files_user_id", table_name="uploaded_files")
    op.drop_index("ix_uploaded_files_id", table_name="uploaded_files")
    op.drop_table("uploaded_files")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

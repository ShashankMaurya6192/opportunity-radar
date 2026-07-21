"""Add intelligence, resume, and matching fields.

Revision ID: 20260721_0002
Revises: 20260721_01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260721_0002"
down_revision = "20260721_01"
branch_labels = None
depends_on = None


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def upgrade() -> None:
    user_profile_columns = _column_names("user_profile")

    if "resume_text" not in user_profile_columns:
        op.add_column(
            "user_profile",
            sa.Column(
                "resume_text",
                sa.Text(),
                nullable=False,
                server_default="",
            ),
        )

    company_columns = _column_names("companies")

    company_additions = [
        ("intelligence_summary", sa.Column(
            "intelligence_summary",
            sa.Text(),
            nullable=False,
            server_default="",
        )),
        ("intelligence_json", sa.Column(
            "intelligence_json",
            sa.Text(),
            nullable=False,
            server_default="",
        )),
        ("company_type", sa.Column(
            "company_type",
            sa.String(120),
            nullable=False,
            server_default="",
        )),
        ("estimated_size", sa.Column(
            "estimated_size",
            sa.String(80),
            nullable=False,
            server_default="",
        )),
        ("hiring_probability", sa.Column(
            "hiring_probability",
            sa.Integer(),
            nullable=False,
            server_default="0",
        )),
        ("engineering_maturity", sa.Column(
            "engineering_maturity",
            sa.Integer(),
            nullable=False,
            server_default="0",
        )),
        ("outreach_probability", sa.Column(
            "outreach_probability",
            sa.Integer(),
            nullable=False,
            server_default="0",
        )),
        ("risk_level", sa.Column(
            "risk_level",
            sa.String(30),
            nullable=False,
            server_default="Low",
        )),
    ]

    for column_name, column in company_additions:
        if column_name not in company_columns:
            op.add_column("companies", column)

    job_columns = _column_names("jobs")

    if "description" not in job_columns:
        op.add_column(
            "jobs",
            sa.Column(
                "description",
                sa.Text(),
                nullable=False,
                server_default="",
            ),
        )

    if "match_details" not in job_columns:
        op.add_column(
            "jobs",
            sa.Column(
                "match_details",
                sa.Text(),
                nullable=False,
                server_default="",
            ),
        )


def downgrade() -> None:
    job_columns = _column_names("jobs")

    for column_name in ("match_details", "description"):
        if column_name in job_columns:
            op.drop_column("jobs", column_name)

    company_columns = _column_names("companies")

    for column_name in (
        "risk_level",
        "outreach_probability",
        "engineering_maturity",
        "hiring_probability",
        "estimated_size",
        "company_type",
        "intelligence_json",
        "intelligence_summary",
    ):
        if column_name in company_columns:
            op.drop_column("companies", column_name)

    user_profile_columns = _column_names("user_profile")

    if "resume_text" in user_profile_columns:
        op.drop_column("user_profile", "resume_text")

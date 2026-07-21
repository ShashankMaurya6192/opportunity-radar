"""Add v0.5 discovery fields and run history."""

from alembic import op
import sqlalchemy as sa


revision = "20260721_01"
down_revision = None
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def upgrade():
    inspector = _inspector()
    table_names = set(inspector.get_table_names())

    if "discovery_campaigns" not in table_names:
        raise RuntimeError(
            "Required table discovery_campaigns does not exist."
        )

    campaign_columns = {
        column["name"]
        for column in inspector.get_columns("discovery_campaigns")
    }

    # SQLite supports ADD COLUMN directly. Avoid batch table rebuilding,
    # which was causing the circular column-ordering error.
    if "remote_only" not in campaign_columns:
        op.add_column(
            "discovery_campaigns",
            sa.Column(
                "remote_only",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )

    if "minimum_score" not in campaign_columns:
        op.add_column(
            "discovery_campaigns",
            sa.Column(
                "minimum_score",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )

    inspector = _inspector()
    table_names = set(inspector.get_table_names())

    if "discovery_runs" not in table_names:
        op.create_table(
            "discovery_runs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "campaign_id",
                sa.Integer(),
                sa.ForeignKey("discovery_campaigns.id"),
                nullable=True,
            ),
            sa.Column("query", sa.String(700), nullable=False),
            sa.Column("status", sa.String(40), nullable=False),
            sa.Column(
                "candidates_found",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "companies_saved",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "errors",
                sa.Text(),
                nullable=False,
                server_default="",
            ),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
        )

    inspector = _inspector()
    existing_indexes = {
        index["name"]
        for index in inspector.get_indexes("discovery_runs")
    }

    if "ix_discovery_runs_campaign_id" not in existing_indexes:
        op.create_index(
            "ix_discovery_runs_campaign_id",
            "discovery_runs",
            ["campaign_id"],
        )


def downgrade():
    inspector = _inspector()
    table_names = set(inspector.get_table_names())

    if "discovery_runs" in table_names:
        existing_indexes = {
            index["name"]
            for index in inspector.get_indexes("discovery_runs")
        }

        if "ix_discovery_runs_campaign_id" in existing_indexes:
            op.drop_index(
                "ix_discovery_runs_campaign_id",
                table_name="discovery_runs",
            )

        op.drop_table("discovery_runs")

    inspector = _inspector()
    table_names = set(inspector.get_table_names())

    if "discovery_campaigns" in table_names:
        campaign_columns = {
            column["name"]
            for column in inspector.get_columns("discovery_campaigns")
        }

        # SQLite requires batch mode for dropping columns on older versions.
        columns_to_drop = [
            name
            for name in ("minimum_score", "remote_only")
            if name in campaign_columns
        ]

        if columns_to_drop:
            with op.batch_alter_table("discovery_campaigns") as batch:
                for column_name in columns_to_drop:
                    batch.drop_column(column_name)

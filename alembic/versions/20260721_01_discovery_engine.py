"""Add v0.5 discovery fields and run history."""
from alembic import op
import sqlalchemy as sa

revision = "20260721_01"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table("discovery_campaigns") as batch:
        batch.add_column(sa.Column("remote_only", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("minimum_score", sa.Integer(), nullable=False, server_default="0"))
    op.create_table(
        "discovery_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("discovery_campaigns.id"), nullable=True),
        sa.Column("query", sa.String(700), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("candidates_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("companies_saved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.Text(), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_discovery_runs_campaign_id", "discovery_runs", ["campaign_id"])

def downgrade():
    op.drop_index("ix_discovery_runs_campaign_id", table_name="discovery_runs")
    op.drop_table("discovery_runs")
    with op.batch_alter_table("discovery_campaigns") as batch:
        batch.drop_column("minimum_score")
        batch.drop_column("remote_only")

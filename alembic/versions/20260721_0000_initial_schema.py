"""Create the initial application schema.

Revision ID: 20260721_0000
Revises:
"""

from alembic import op
from app.database import Base
import app.models  # noqa: F401


revision = "20260721_0000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)

"""default work shift type

Revision ID: 314792047285
Revises: 7c2bd8d3cf3e
Create Date: 2026-11-10 14:41:21.789781
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "314792047285"
down_revision: str | Sequence[str] | None = "7c2bd8d3cf3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "work_shifts",
        "type",
        server_default=sa.text("'morning'"),
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "work_shifts",
        "type",
        server_default=None,
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )

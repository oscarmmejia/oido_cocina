"""add responsible_id to schedules

Revision ID: a7c1d2e3f4b5
Revises: 314792047285
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7c1d2e3f4b5"
down_revision: str | Sequence[str] | None = "314792047285"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "schedules",
        sa.Column("responsible_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_schedules_responsible_id",
        "schedules",
        "employees",
        ["responsible_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_schedules_responsible_id",
        "schedules",
        type_="foreignkey",
    )
    op.drop_column("schedules", "responsible_id")

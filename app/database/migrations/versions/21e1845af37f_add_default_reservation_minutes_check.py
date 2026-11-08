"""add default reservation minutes check

Revision ID: 21e1845af37f
Revises: 652bcc68cd94
Create Date: 2026-11-08 20:58:36.606223

The model already declares this constraint (`RestaurantSettings`), but the
`default_reservation_minutes` column was added in 652bcc68cd94 without it.
Alembic does not compare check constraints on autogenerate, so the gap was not
detected by `alembic check`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21e1845af37f'
down_revision: Union[str, None] = '652bcc68cd94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT_NAME = "ck_restaurant_settings_default_reservation_minutes_positive"


def upgrade() -> None:
    op.create_check_constraint(
        op.f(CONSTRAINT_NAME),
        "restaurant_settings",
        "default_reservation_minutes > 0",
    )


def downgrade() -> None:
    op.drop_constraint(op.f(CONSTRAINT_NAME), "restaurant_settings", type_="check")

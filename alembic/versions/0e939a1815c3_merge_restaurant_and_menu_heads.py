"""merge restaurant and menu heads

Revision ID: 0e939a1815c3
Revises: 4f2d7c91ab06, e773e1d3e1e9
Create Date: 2026-11-05 17:29:41.691210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e939a1815c3'
down_revision: Union[str, Sequence[str], None] = ('4f2d7c91ab06', 'e773e1d3e1e9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

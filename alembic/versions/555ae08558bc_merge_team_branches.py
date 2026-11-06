"""merge team branches

Revision ID: 555ae08558bc
Revises: 3bad8d950244, 4f2d7c91ab06
Create Date: 2026-11-05 11:00:37.528710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '555ae08558bc'
down_revision: Union[str, Sequence[str], None] = ('3bad8d950244', '4f2d7c91ab06')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

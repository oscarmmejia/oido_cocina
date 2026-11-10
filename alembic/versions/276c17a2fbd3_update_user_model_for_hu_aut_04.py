"""update user model for HU-AUT-04

Revision ID: 276c17a2fbd3
Revises: 555ae08558bc
Create Date: 2026-11-05 11:08:04.531318

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '276c17a2fbd3'
down_revision: Union[str, Sequence[str], None] = '555ae08558bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.alter_column('users', 'hashed_password', new_column_name='password_hash')
    op.add_column('users', sa.Column('name', sa.String(), nullable=False, server_default='Usuario Existente'))
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('role_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'users', 'restaurant', ['restaurant_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'role_id')
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'name')
    op.alter_column('users', 'password_hash', new_column_name='hashed_password')
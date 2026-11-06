from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1f2a3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '269faa41e9e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('shifts',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('schedule_id', sa.Integer(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
    sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shifts_id'), 'shifts', ['id'], unique=False)
    op.create_index(op.f('ix_shifts_schedule_id'), 'shifts', ['schedule_id'], unique=False)
    op.create_index(op.f('ix_shifts_employee_id'), 'shifts', ['employee_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_shifts_employee_id'), table_name='shifts')
    op.drop_index(op.f('ix_shifts_schedule_id'), table_name='shifts')
    op.drop_index(op.f('ix_shifts_id'), table_name='shifts')
    op.drop_table('shifts')
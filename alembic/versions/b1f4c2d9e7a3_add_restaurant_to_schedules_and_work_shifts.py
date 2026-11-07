"""add restaurant to schedules and create work_shifts

Revision ID: b1f4c2d9e7a3
Revises: 269faa41e9e5
Create Date: 2026-11-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1f4c2d9e7a3"
down_revision: Union[str, Sequence[str], None] = "269faa41e9e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) El cuadrante pertenece a un restaurante (aislamiento entre restaurantes).
    #    Se rellena desde el empleado responsable, sin valores fijos.
    op.add_column("schedules", sa.Column("restaurant_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE schedules AS s
        SET restaurant_id = e.restaurant_id
        FROM employees AS e
        WHERE e.id = s.responsible_id
        """
    )
    op.alter_column("schedules", "restaurant_id", nullable=False)
    op.create_foreign_key(
        "fk_schedules_restaurant_id", "schedules", "restaurant",
        ["restaurant_id"], ["id"], ondelete="CASCADE",
    )
    op.create_index(op.f("ix_schedules_restaurant_id"), "schedules", ["restaurant_id"])
    op.create_check_constraint(
        "ck_schedule_period_order", "schedules", "period_start <= period_end"
    )
    op.create_check_constraint(
        "ck_schedule_status", "schedules", "status IN ('borrador', 'publicado')"
    )

    # 2) Turnos de trabajo
    op.create_table(
        "work_shifts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name="ck_work_shift_time_order"),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
    )
    op.create_index(op.f("ix_work_shifts_schedule_id"), "work_shifts", ["schedule_id"])
    op.create_index(
        "ix_work_shifts_employee_starts", "work_shifts", ["employee_id", "starts_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_work_shifts_employee_starts", table_name="work_shifts")
    op.drop_index(op.f("ix_work_shifts_schedule_id"), table_name="work_shifts")
    op.drop_table("work_shifts")

    op.drop_constraint("ck_schedule_status", "schedules", type_="check")
    op.drop_constraint("ck_schedule_period_order", "schedules", type_="check")
    op.drop_index(op.f("ix_schedules_restaurant_id"), table_name="schedules")
    op.drop_constraint("fk_schedules_restaurant_id", "schedules", type_="foreignkey")
    op.drop_column("schedules", "restaurant_id")

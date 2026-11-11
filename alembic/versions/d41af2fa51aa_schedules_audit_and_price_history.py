"""schedules audit and price history

Revision ID: d41af2fa51aa
Revises: 5999601d641f
Create Date: 2026-11-06 21:32:05.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d41af2fa51aa"
down_revision: str | Sequence[str] | None = "5999601d641f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("job_position", sa.String(length=50), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "job_position IN ('cook', 'waiter', 'manager', 'host', 'other')",
            name="ck_employees_job_position",
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_employees_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_employees_user_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_employees"),
        sa.UniqueConstraint(
            "restaurant_id",
            "user_id",
            name="uq_employees_restaurant_user",
        ),
    )
    op.create_index("ix_employees_restaurant_id", "employees", ["restaurant_id"])

    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("published_by_user_id", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "period_end >= period_start",
            name="ck_schedules_period_range",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published')",
            name="ck_schedules_status",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_schedules_created_by_user_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["published_by_user_id"],
            ["users.id"],
            name="fk_schedules_published_by_user_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_schedules_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_schedules"),
        sa.UniqueConstraint(
            "restaurant_id",
            "period_start",
            "period_end",
            name="uq_schedules_restaurant_period",
        ),
    )
    op.create_index("ix_schedules_restaurant_id", "schedules", ["restaurant_id"])
    op.create_index(
        "ix_schedules_restaurant_period",
        "schedules",
        ["restaurant_id", "period_start"],
    )

    op.create_table(
        "work_shifts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="scheduled",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_work_shifts_time_range",
        ),
        sa.CheckConstraint(
            "type IN ('morning', 'afternoon', 'night', 'split')",
            name="ck_work_shifts_type",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'confirmed', 'cancelled')",
            name="ck_work_shifts_status",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name="fk_work_shifts_employee_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["schedule_id"],
            ["schedules.id"],
            name="fk_work_shifts_schedule_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_work_shifts"),
    )
    op.create_index("ix_work_shifts_employee_id", "work_shifts", ["employee_id"])
    op.create_index("ix_work_shifts_schedule_id", "work_shifts", ["schedule_id"])

    op.create_table(
        "time_off_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("resolved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_time_off_requests_time_range",
        ),
        sa.CheckConstraint(
            "type IN ('vacation', 'sick_leave', 'personal', 'other')",
            name="ck_time_off_requests_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="ck_time_off_requests_status",
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employees.id"],
            name="fk_time_off_requests_employee_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_user_id"],
            ["users.id"],
            name="fk_time_off_requests_resolved_by_user_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_time_off_requests"),
    )
    op.create_index(
        "ix_time_off_requests_employee_id",
        "time_off_requests",
        ["employee_id"],
    )
    op.create_index(
        "ix_time_off_requests_employee_status",
        "time_off_requests",
        ["employee_id", "status"],
    )

    op.create_table(
        "shift_swap_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("origin_shift_id", sa.Integer(), nullable=False),
        sa.Column("target_shift_id", sa.Integer(), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("resolved_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "target_shift_id IS NULL OR target_shift_id <> origin_shift_id",
            name="ck_shift_swap_requests_distinct_shifts",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="ck_shift_swap_requests_status",
        ),
        sa.ForeignKeyConstraint(
            ["origin_shift_id"],
            ["work_shifts.id"],
            name="fk_shift_swap_requests_origin_shift_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_user_id"],
            ["users.id"],
            name="fk_shift_swap_requests_requested_by_user_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_user_id"],
            ["users.id"],
            name="fk_shift_swap_requests_resolved_by_user_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_shift_id"],
            ["work_shifts.id"],
            name="fk_shift_swap_requests_target_shift_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_shift_swap_requests"),
    )
    op.create_index(
        "ix_shift_swap_requests_status",
        "shift_swap_requests",
        ["status"],
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_name", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column(
            "old_values",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "new_values",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "result",
            sa.String(length=20),
            server_default="success",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_audit_logs_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_audit_logs_user_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.create_index(
        "ix_audit_logs_restaurant_created",
        "audit_logs",
        ["restaurant_id", "created_at"],
    )
    op.create_index(
        "ix_audit_logs_entity",
        "audit_logs",
        ["entity_name", "entity_id"],
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])

    op.create_table(
        "price_history",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=10), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("old_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("new_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "entity_type IN ('dish', 'menu')",
            name="ck_price_history_entity_type",
        ),
        sa.CheckConstraint(
            "old_price >= 0",
            name="ck_price_history_old_price_non_negative",
        ),
        sa.CheckConstraint(
            "new_price >= 0",
            name="ck_price_history_new_price_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_user_id"],
            ["users.id"],
            name="fk_price_history_changed_by_user_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_price_history_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_price_history"),
    )
    op.create_index(
        "ix_price_history_entity_created",
        "price_history",
        ["entity_type", "entity_id", "created_at"],
    )
    op.create_index(
        "ix_price_history_restaurant_created",
        "price_history",
        ["restaurant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("price_history")
    op.drop_table("audit_logs")
    op.drop_table("shift_swap_requests")
    op.drop_table("time_off_requests")
    op.drop_table("work_shifts")
    op.drop_table("schedules")
    op.drop_table("employees")

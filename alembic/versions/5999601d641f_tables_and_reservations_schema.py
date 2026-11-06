"""tables and reservations schema

Revision ID: 5999601d641f
Revises: 040bdaa5e468
Create Date: 2026-11-06 21:32:04.500000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5999601d641f"
down_revision: str | Sequence[str] | None = "040bdaa5e468"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _create_tables_table() -> None:
    op.create_table(
        "tables",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("min_capacity", sa.Integer(), nullable=False),
        sa.Column("max_capacity", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=10), nullable=False),
        sa.Column(
            "is_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "is_capacity_adjustable",
            sa.Boolean(),
            server_default=sa.text("false"),
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
            "min_capacity >= 1",
            name="ck_table_min_capacity",
        ),
        sa.CheckConstraint(
            "max_capacity >= min_capacity",
            name="ck_table_capacity_range",
        ),
        sa.CheckConstraint(
            "location IN ('interior', 'exterior', 'bar')",
            name="ck_table_location",
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_tables_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tables"),
        sa.UniqueConstraint(
            "restaurant_id",
            "number",
            name="uq_table_restaurant_number",
        ),
    )
    op.create_index("ix_tables_restaurant_id", "tables", ["restaurant_id"])


def _normalize_existing_tables_table() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("tables")}

    if "is_active" in columns:
        op.alter_column(
            "tables",
            "is_active",
            new_column_name="is_enabled",
            existing_type=sa.Boolean(),
            existing_nullable=False,
        )
    if "adjustable_capacity" in columns:
        op.alter_column(
            "tables",
            "adjustable_capacity",
            new_column_name="is_capacity_adjustable",
            existing_type=sa.Boolean(),
            existing_nullable=False,
        )
    if "created_at" not in columns:
        op.add_column(
            "tables",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
    if "updated_at" not in columns:
        op.add_column(
            "tables",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    for constraint_name in (
        "ck_table_location",
        "ck_table_min_capacity",
        "ck_table_capacity_range",
    ):
        op.execute(
            f'ALTER TABLE "tables" DROP CONSTRAINT IF EXISTS "{constraint_name}"'
        )

    op.create_check_constraint(
        "ck_table_min_capacity",
        "tables",
        "min_capacity >= 1",
    )
    op.create_check_constraint(
        "ck_table_capacity_range",
        "tables",
        "max_capacity >= min_capacity",
    )
    op.create_check_constraint(
        "ck_table_location",
        "tables",
        "location IN ('interior', 'exterior', 'bar')",
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("tables"):
        _normalize_existing_tables_table()
    else:
        _create_tables_table()

    op.create_table(
        "table_combinations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column(
            "is_enabled",
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
            "capacity >= 1",
            name="ck_table_combinations_capacity",
        ),
        sa.CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_table_combinations_valid_range",
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_table_combinations_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_table_combinations"),
        sa.UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_table_combinations_restaurant_name",
        ),
    )
    op.create_index(
        "ix_table_combinations_restaurant_id",
        "table_combinations",
        ["restaurant_id"],
    )

    op.create_table(
        "table_combination_tables",
        sa.Column("combination_id", sa.Integer(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["combination_id"],
            ["table_combinations.id"],
            name="fk_table_combination_tables_combination_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["table_id"],
            ["tables.id"],
            name="fk_table_combination_tables_table_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "combination_id",
            "table_id",
            name="pk_table_combination_tables",
        ),
    )
    op.create_index(
        "ix_table_combination_tables_table_id",
        "table_combination_tables",
        ["table_id"],
    )

    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("combination_id", sa.Integer(), nullable=True),
        sa.Column("customer_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("party_size", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
            "party_size >= 1",
            name="ck_reservations_party_size",
        ),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_reservations_time_range",
        ),
        sa.CheckConstraint(
            "status IN ("
            "'pending', 'confirmed', 'seated', 'completed', "
            "'cancelled', 'no_show'"
            ")",
            name="ck_reservations_status",
        ),
        sa.ForeignKeyConstraint(
            ["combination_id"],
            ["table_combinations.id"],
            name="fk_reservations_combination_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_reservations_created_by_user_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_reservations_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reservations"),
    )
    op.create_index(
        "ix_reservations_restaurant_id",
        "reservations",
        ["restaurant_id"],
    )
    op.create_index(
        "ix_reservations_restaurant_start",
        "reservations",
        ["restaurant_id", "start_at"],
    )
    op.create_index(
        "ix_reservations_restaurant_phone_start",
        "reservations",
        ["restaurant_id", "phone", "start_at"],
    )

    op.create_table(
        "reservation_tables",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reservation_id", sa.Integer(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.CheckConstraint(
            "end_at > start_at",
            name="ck_reservation_tables_time_range",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'cancelled')",
            name="ck_reservation_tables_status",
        ),
        sa.ForeignKeyConstraint(
            ["reservation_id"],
            ["reservations.id"],
            name="fk_reservation_tables_reservation_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["table_id"],
            ["tables.id"],
            name="fk_reservation_tables_table_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reservation_tables"),
        sa.UniqueConstraint(
            "reservation_id",
            "table_id",
            name="uq_reservation_tables_reservation_table",
        ),
    )
    op.create_index(
        "ix_reservation_tables_table_id",
        "reservation_tables",
        ["table_id"],
    )
    op.create_index(
        "ix_reservation_tables_reservation_id",
        "reservation_tables",
        ["reservation_id"],
    )

    op.create_table(
        "reservation_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reservation_id", sa.Integer(), nullable=False),
        sa.Column("previous_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_user_id"],
            ["users.id"],
            name="fk_reservation_status_history_changed_by_user_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reservation_id"],
            ["reservations.id"],
            name="fk_reservation_status_history_reservation_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reservation_status_history"),
    )
    op.create_index(
        "ix_reservation_status_history_reservation",
        "reservation_status_history",
        ["reservation_id", "changed_at"],
    )


def downgrade() -> None:
    op.drop_table("reservation_status_history")
    op.drop_table("reservation_tables")
    op.drop_table("reservations")
    op.drop_table("table_combination_tables")
    op.drop_table("table_combinations")
    op.drop_table("tables")

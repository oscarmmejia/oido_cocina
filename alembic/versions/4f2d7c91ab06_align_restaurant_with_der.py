"""Unify Restaurant and RestaurantSettings according to the updated DER.

Revision ID: 4f2d7c91ab06
Revises: 84d4e0fbe03a
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "4f2d7c91ab06"
down_revision: str | None = "84d4e0fbe03a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # PostgreSQL conserva los ids y adapta las FK al renombrar una tabla.
    op.rename_table("restaurants", "restaurant")
    op.alter_column(
        "restaurant", "timezone",
        new_column_name="time_zone",
        existing_type=sa.String(length=64),
        existing_nullable=False,
    )
    op.add_column("restaurant", sa.Column(
        "curtesy_minutes", sa.Integer(), nullable=False, server_default=sa.text("5")
    ))
    op.add_column("restaurant", sa.Column(
        "slot_minutes", sa.Integer(), nullable=False, server_default=sa.text("60")
    ))
    op.add_column("restaurant", sa.Column("min_break_between_shifts", sa.Integer()))
    op.add_column("restaurant", sa.Column("day_of_week", sa.Integer()))
    op.add_column("restaurant", sa.Column("period", sa.String(length=16)))
    op.add_column("restaurant", sa.Column("open_time", sa.Time()))
    op.add_column("restaurant", sa.Column("close_time", sa.Time()))
    op.add_column("restaurant", sa.Column("kitchen_close_time", sa.Time()))
    op.add_column("restaurant", sa.Column("direction", sa.String(length=255)))

    # Conservar tiempos previamente registrados, si los hubiera.
    op.execute("""
        UPDATE restaurant AS r
        SET curtesy_minutes = s.courtesy_minutes,
            slot_minutes = s.slot_minutes
        FROM restaurant_settings AS s
        WHERE s.restaurant_id = r.id
    """)

    op.create_check_constraint(
        "ck_restaurant_curtesy_nonnegative", "restaurant", "curtesy_minutes >= 0"
    )
    op.create_check_constraint(
        "ck_restaurant_slot_positive", "restaurant", "slot_minutes > 0"
    )
    op.create_check_constraint(
        "ck_restaurant_min_break_nonnegative", "restaurant",
        "min_break_between_shifts IS NULL OR min_break_between_shifts >= 0",
    )
    op.create_check_constraint(
        "ck_restaurant_day_of_week", "restaurant",
        "day_of_week IS NULL OR day_of_week BETWEEN 1 AND 7",
    )

    # Ya se han copiado los tiempos necesarios a restaurant.
    # default_reservation_minutes desaparece por decisión del equipo.
    op.drop_table("restaurant_settings")
    # El DER no incluye estos campos en restaurant.
    op.drop_column("restaurant", "created_at")
    op.drop_column("restaurant", "updated_at")
    op.alter_column("restaurant", "is_active", server_default=sa.text("true"),
                    existing_type=sa.Boolean(), existing_nullable=False)


def downgrade() -> None:
    # El downgrade restaura el esquema, NO los antiguos valores de
    # default_reservation_minutes ni las marcas temporales originales.
    op.add_column("restaurant", sa.Column(
        "created_at", sa.DateTime(timezone=True),
        server_default=sa.text("now()"), nullable=False,
    ))
    op.add_column("restaurant", sa.Column(
        "updated_at", sa.DateTime(timezone=True),
        server_default=sa.text("now()"), nullable=False,
    ))
    op.create_table(
        "restaurant_settings",
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("courtesy_minutes", sa.Integer(), nullable=False),
        sa.Column("slot_minutes", sa.Integer(), nullable=False),
        sa.Column("default_reservation_minutes", sa.Integer(), nullable=False),
        sa.CheckConstraint("courtesy_minutes >= 0"),
        sa.CheckConstraint("slot_minutes > 0"),
        sa.CheckConstraint("default_reservation_minutes > 0"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurant.id"]),
        sa.PrimaryKeyConstraint("restaurant_id"),
    )
    # Al no existir ya un valor independiente, reconstruimos el antiguo
    # default_reservation_minutes con slot_minutes (acuerdo del equipo).
    op.execute("""
        INSERT INTO restaurant_settings
            (restaurant_id, courtesy_minutes, slot_minutes, default_reservation_minutes)
        SELECT id, curtesy_minutes, slot_minutes, slot_minutes
        FROM restaurant
    """)

    for name in (
        "ck_restaurant_curtesy_nonnegative",
        "ck_restaurant_slot_positive",
        "ck_restaurant_min_break_nonnegative",
        "ck_restaurant_day_of_week",
    ):
        op.drop_constraint(name, "restaurant", type_="check")

    for name in (
        "curtesy_minutes", "slot_minutes", "min_break_between_shifts",
        "day_of_week", "period", "open_time", "close_time",
        "kitchen_close_time", "direction",
    ):
        op.drop_column("restaurant", name)

    op.alter_column("restaurant", "is_active", server_default=None,
                    existing_type=sa.Boolean(), existing_nullable=False)
    op.alter_column(
        "restaurant", "time_zone",
        new_column_name="timezone",
        existing_type=sa.String(length=64),
        existing_nullable=False,
    )
    op.rename_table("restaurant", "restaurants")

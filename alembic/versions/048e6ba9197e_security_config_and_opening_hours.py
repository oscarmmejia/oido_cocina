"""security config and opening hours

Revision ID: 048e6ba9197e
Revises: 0e939a1815c3
Create Date: 2026-11-06 21:32:03.901086
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "048e6ba9197e"
down_revision: str | Sequence[str] | None = "0e939a1815c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "opening_hours",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("period", sa.String(length=16), nullable=False),
        sa.Column("open_time", sa.Time(), nullable=False),
        sa.Column("close_time", sa.Time(), nullable=False),
        sa.Column("kitchen_close_time", sa.Time(), nullable=True),
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
            "day_of_week BETWEEN 1 AND 7",
            name="ck_opening_hours_day_of_week",
        ),
        sa.CheckConstraint(
            "period IN ('morning', 'afternoon')",
            name="ck_opening_hours_period",
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_opening_hours_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_opening_hours"),
        sa.UniqueConstraint(
            "restaurant_id",
            "day_of_week",
            "period",
            name="uq_opening_hours_restaurant_day_period",
        ),
    )
    op.create_index(
        "ix_opening_hours_restaurant_id",
        "opening_hours",
        ["restaurant_id"],
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_roles_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_roles_restaurant_name",
        ),
    )
    op.create_index("ix_roles_restaurant_id", "roles", ["restaurant_id"])

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_permissions"),
        sa.UniqueConstraint("name", name="uq_permissions_name"),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name="fk_role_permissions_permission_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_role_permissions_role_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "role_id",
            "permission_id",
            name="pk_role_permissions",
        ),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=30), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "token_version",
            sa.Integer(),
            server_default=sa.text("0"),
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
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_users_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name="fk_users_role_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_restaurant_id", "users", ["restaurant_id"])
    op.create_index("ix_users_role_id", "users", ["role_id"])
    op.create_index(
        "uq_users_email_lower",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )

    # Mover los horarios existentes de restaurant a opening_hours.
    op.execute(
        """
        INSERT INTO opening_hours (
            restaurant_id,
            day_of_week,
            period,
            open_time,
            close_time,
            kitchen_close_time,
            is_active,
            created_at,
            updated_at
        )
        SELECT
            id,
            day_of_week,
            period,
            open_time,
            close_time,
            kitchen_close_time,
            true,
            now(),
            now()
        FROM restaurant
        WHERE day_of_week IS NOT NULL
          AND period IN ('morning', 'afternoon')
          AND open_time IS NOT NULL
          AND close_time IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )

    op.drop_constraint(
        "ck_restaurant_day_of_week",
        "restaurant",
        type_="check",
    )
    op.drop_column("restaurant", "day_of_week")
    op.drop_column("restaurant", "period")
    op.drop_column("restaurant", "open_time")
    op.drop_column("restaurant", "close_time")
    op.drop_column("restaurant", "kitchen_close_time")

    op.add_column(
        "restaurant",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "restaurant",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column(
        "restaurant",
        "time_zone",
        server_default=sa.text("'Europe/Madrid'"),
        existing_type=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.add_column(
        "restaurant",
        sa.Column("day_of_week", sa.Integer(), nullable=True),
    )
    op.add_column(
        "restaurant",
        sa.Column("period", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "restaurant",
        sa.Column("open_time", sa.Time(), nullable=True),
    )
    op.add_column(
        "restaurant",
        sa.Column("close_time", sa.Time(), nullable=True),
    )
    op.add_column(
        "restaurant",
        sa.Column("kitchen_close_time", sa.Time(), nullable=True),
    )

    op.execute(
        """
        UPDATE restaurant AS r
        SET
            day_of_week = oh.day_of_week,
            period = oh.period,
            open_time = oh.open_time,
            close_time = oh.close_time,
            kitchen_close_time = oh.kitchen_close_time
        FROM (
            SELECT DISTINCT ON (restaurant_id)
                restaurant_id,
                day_of_week,
                period,
                open_time,
                close_time,
                kitchen_close_time
            FROM opening_hours
            ORDER BY restaurant_id, day_of_week, period
        ) AS oh
        WHERE oh.restaurant_id = r.id
        """
    )

    op.create_check_constraint(
        "ck_restaurant_day_of_week",
        "restaurant",
        "day_of_week IS NULL OR day_of_week BETWEEN 1 AND 7",
    )

    op.drop_column("restaurant", "updated_at")
    op.drop_column("restaurant", "created_at")
    op.alter_column(
        "restaurant",
        "time_zone",
        server_default=None,
        existing_type=sa.String(length=64),
        existing_nullable=False,
    )

    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("opening_hours")

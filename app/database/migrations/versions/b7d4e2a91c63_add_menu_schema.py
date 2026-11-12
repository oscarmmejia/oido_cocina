"""add menu schema

Revision ID: b7d4e2a91c63
Revises: 21e1845af37f
Create Date: 2026-11-09 00:00:00.000000

Creates the five menu tables that were still missing: dishes, dish_allergens,
menu_collections, menus and menu_dishes.

Decisions recorded in docs/der-carta-menus.md:
- `is_required` lives only in `menu_dishes`.
- The included drink is `menu_dishes.role = 'drink'` plus `includes_drink`.
- Validity lives only in `menu_collections`, is inclusive on both ends,
  allows a single day and allows overlaps.
- Business foreign keys are NO ACTION; association foreign keys are CASCADE.
- Cross-restaurant consistency is validated by the application, not the database.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7d4e2a91c63"
down_revision: Union[str, None] = "21e1845af37f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dishes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "is_published",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_available",
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
            "price >= 0",
            name=op.f("ck_dishes_price_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurants.id"],
            name=op.f("fk_dishes_restaurant_id_restaurants"),
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_dishes_category_id_categories"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dishes")),
    )
    op.create_index(op.f("ix_dishes_restaurant_id"), "dishes", ["restaurant_id"])
    op.create_index(op.f("ix_dishes_category_id"), "dishes", ["category_id"])

    op.create_table(
        "dish_allergens",
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("allergen_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["dish_id"],
            ["dishes.id"],
            name=op.f("fk_dish_allergens_dish_id_dishes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["allergen_id"],
            ["allergens.id"],
            name=op.f("fk_dish_allergens_allergen_id_allergens"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "dish_id",
            "allergen_id",
            name=op.f("pk_dish_allergens"),
        ),
    )

    op.create_table(
        "menu_collections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("restaurant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
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
            "type IN ('daily', 'seasonal', 'fixed')",
            name=op.f("ck_menu_collections_type"),
        ),
        sa.CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name=op.f("ck_menu_collections_valid_range"),
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurants.id"],
            name=op.f("fk_menu_collections_restaurant_id_restaurants"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_menu_collections")),
        sa.UniqueConstraint(
            "restaurant_id",
            "name",
            name=op.f("uq_menu_collections_restaurant_id_name"),
        ),
    )
    op.create_index(
        op.f("ix_menu_collections_restaurant_id"),
        "menu_collections",
        ["restaurant_id"],
    )

    op.create_table(
        "menus",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("own_price", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "is_available",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("inactive_reason", sa.String(length=255), nullable=True),
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
            "own_price >= 0",
            name=op.f("ck_menus_own_price_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["menu_collections.id"],
            name=op.f("fk_menus_collection_id_menu_collections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_menus")),
        sa.UniqueConstraint(
            "collection_id",
            "name",
            name=op.f("uq_menus_collection_id_name"),
        ),
    )
    op.create_index(op.f("ix_menus_collection_id"), "menus", ["collection_id"])

    op.create_table(
        "menu_dishes",
        sa.Column("menu_id", sa.Integer(), nullable=False),
        sa.Column("dish_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "is_required",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "includes_drink",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('starter', 'main', 'dessert', 'drink', 'other')",
            name=op.f("ck_menu_dishes_role"),
        ),
        sa.ForeignKeyConstraint(
            ["menu_id"],
            ["menus.id"],
            name=op.f("fk_menu_dishes_menu_id_menus"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["dish_id"],
            ["dishes.id"],
            name=op.f("fk_menu_dishes_dish_id_dishes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "menu_id",
            "dish_id",
            name=op.f("pk_menu_dishes"),
        ),
    )


def downgrade() -> None:
    op.drop_table("menu_dishes")
    op.drop_table("menus")
    op.drop_table("menu_collections")
    op.drop_table("dish_allergens")
    op.drop_table("dishes")

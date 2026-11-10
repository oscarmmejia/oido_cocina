"""normalize menu schema

Revision ID: 040bdaa5e468
Revises: 048e6ba9197e
Create Date: 2026-11-06 21:32:04.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "040bdaa5e468"
down_revision: str | Sequence[str] | None = "048e6ba9197e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.rename_table("Allergen", "allergens")
    op.rename_table("Category", "categories")
    op.rename_table("Dish", "dishes")
    op.rename_table("DishAllergen", "dish_allergens")

    op.alter_column(
        "categories",
        "restaurantId",
        new_column_name="restaurant_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "categories",
        "sortOrder",
        new_column_name="sort_order",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "categories",
        "isActive",
        new_column_name="is_active",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "restaurantId",
        new_column_name="restaurant_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "categoryId",
        new_column_name="category_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "isActive",
        new_column_name="is_active",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "isPublished",
        new_column_name="is_published",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "isAvailable",
        new_column_name="is_available",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "dish_allergens",
        "dishId",
        new_column_name="dish_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "dish_allergens",
        "allergenId",
        new_column_name="allergen_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )

    for table_name in ("allergens", "categories", "dishes"):
        op.add_column(
            table_name,
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.add_column(
            table_name,
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    op.create_foreign_key(
        "fk_categories_restaurant_id",
        "categories",
        "restaurant",
        ["restaurant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_dishes_restaurant_id",
        "dishes",
        "restaurant",
        ["restaurant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_categories_restaurant_id",
        "categories",
        ["restaurant_id"],
    )
    op.create_index(
        "ix_dishes_restaurant_id",
        "dishes",
        ["restaurant_id"],
    )
    op.create_index(
        "ix_dishes_category_id",
        "dishes",
        ["category_id"],
    )

    op.drop_constraint(
        "uq_category_restaurant_name",
        "categories",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_categories_restaurant_name",
        "categories",
        ["restaurant_id", "name"],
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
            name="ck_menu_collections_type",
        ),
        sa.CheckConstraint(
            "valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from",
            name="ck_menu_collections_valid_range",
        ),
        sa.ForeignKeyConstraint(
            ["restaurant_id"],
            ["restaurant.id"],
            name="fk_menu_collections_restaurant_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_menu_collections"),
        sa.UniqueConstraint(
            "restaurant_id",
            "name",
            name="uq_menu_collections_restaurant_name",
        ),
    )
    op.create_index(
        "ix_menu_collections_restaurant_id",
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
            name="ck_menus_own_price_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["collection_id"],
            ["menu_collections.id"],
            name="fk_menus_collection_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_menus"),
        sa.UniqueConstraint(
            "collection_id",
            "name",
            name="uq_menus_collection_name",
        ),
    )
    op.create_index("ix_menus_collection_id", "menus", ["collection_id"])

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
            name="ck_menu_dishes_role",
        ),
        sa.ForeignKeyConstraint(
            ["dish_id"],
            ["dishes.id"],
            name="fk_menu_dishes_dish_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["menu_id"],
            ["menus.id"],
            name="fk_menu_dishes_menu_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "menu_id",
            "dish_id",
            name="pk_menu_dishes",
        ),
    )


def downgrade() -> None:
    op.drop_table("menu_dishes")
    op.drop_table("menus")
    op.drop_table("menu_collections")

    op.drop_index("ix_dishes_category_id", table_name="dishes")
    op.drop_index("ix_dishes_restaurant_id", table_name="dishes")
    op.drop_index("ix_categories_restaurant_id", table_name="categories")

    op.drop_constraint("fk_dishes_restaurant_id", "dishes", type_="foreignkey")
    op.drop_constraint(
        "fk_categories_restaurant_id",
        "categories",
        type_="foreignkey",
    )

    for table_name in ("allergens", "categories", "dishes"):
        op.drop_column(table_name, "updated_at")
        op.drop_column(table_name, "created_at")

    op.drop_constraint(
        "uq_categories_restaurant_name",
        "categories",
        type_="unique",
    )

    op.alter_column(
        "categories",
        "restaurant_id",
        new_column_name="restaurantId",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "categories",
        "sort_order",
        new_column_name="sortOrder",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "categories",
        "is_active",
        new_column_name="isActive",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "restaurant_id",
        new_column_name="restaurantId",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "category_id",
        new_column_name="categoryId",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "is_active",
        new_column_name="isActive",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "is_published",
        new_column_name="isPublished",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "dishes",
        "is_available",
        new_column_name="isAvailable",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
    op.alter_column(
        "dish_allergens",
        "dish_id",
        new_column_name="dishId",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.alter_column(
        "dish_allergens",
        "allergen_id",
        new_column_name="allergenId",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )

    op.create_unique_constraint(
        "uq_category_restaurant_name",
        "categories",
        ["restaurantId", "name"],
    )

    op.rename_table("dish_allergens", "DishAllergen")
    op.rename_table("dishes", "Dish")
    op.rename_table("categories", "Category")
    op.rename_table("allergens", "Allergen")

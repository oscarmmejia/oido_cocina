"""create initial restaurant tables

Revision ID: e773e1d3e1e9
Revises: 
Create Date: 2026-11-04 16:52:43.281583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e773e1d3e1e9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('Allergen',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('code', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('name')
    )
    op.create_table('Category',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('restaurantId', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('sortOrder', sa.Integer(), nullable=False),
    sa.Column('isActive', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('restaurantId', 'name', name='uq_category_restaurant_name')
    )
    op.create_table('Dish',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('restaurantId', sa.Integer(), nullable=False),
    sa.Column('categoryId', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('isActive', sa.Boolean(), nullable=False),
    sa.Column('isPublished', sa.Boolean(), nullable=False),
    sa.Column('isAvailable', sa.Boolean(), nullable=False),
    sa.CheckConstraint('price >= 0', name='ck_dish_price_non_negative'),
    sa.ForeignKeyConstraint(['categoryId'], ['Category.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('DishAllergen',
    sa.Column('dishId', sa.Integer(), nullable=False),
    sa.Column('allergenId', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['allergenId'], ['Allergen.id'], ),
    sa.ForeignKeyConstraint(['dishId'], ['Dish.id'], ),
    sa.PrimaryKeyConstraint('dishId', 'allergenId')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('DishAllergen')
    op.drop_table('Dish')
    op.drop_table('Category')
    op.drop_table('Allergen')

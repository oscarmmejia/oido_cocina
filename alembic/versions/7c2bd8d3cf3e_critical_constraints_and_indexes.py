"""critical constraints and indexes

Revision ID: 7c2bd8d3cf3e
Revises: d41af2fa51aa
Create Date: 2026-11-06 21:32:24.644537
"""

from collections.abc import Sequence

from alembic import op

revision: str = "7c2bd8d3cf3e"
down_revision: str | Sequence[str] | None = "d41af2fa51aa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.execute(
        """
        ALTER TABLE reservation_tables
        ADD CONSTRAINT ex_reservation_tables_no_overlap
        EXCLUDE USING gist (
            table_id WITH =,
            tstzrange(start_at, end_at) WITH &&
        )
        WHERE (status = 'active')
        """
    )

    op.execute(
        """
        ALTER TABLE work_shifts
        ADD CONSTRAINT ex_work_shifts_no_overlap
        EXCLUDE USING gist (
            employee_id WITH =,
            tstzrange(start_at, end_at) WITH &&
        )
        WHERE (status <> 'cancelled')
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX uq_reservations_active_contact_date
        ON reservations (
            restaurant_id,
            COALESCE(lower(email), phone),
            ((start_at AT TIME ZONE 'UTC')::date)
        )
        WHERE status IN ('pending', 'confirmed')
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_reservations_active_contact_date")
    op.execute(
        "ALTER TABLE work_shifts "
        "DROP CONSTRAINT IF EXISTS ex_work_shifts_no_overlap"
    )
    op.execute(
        "ALTER TABLE reservation_tables "
        "DROP CONSTRAINT IF EXISTS ex_reservation_tables_no_overlap"
    )

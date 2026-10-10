"""Add parking lot currency and reliable admin identifiers.

Revision ID: 0002_local_app
Revises: 0001_initial
Create Date: 2026-10-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_local_app"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "parking_lot",
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
    )

    op.execute("CREATE SEQUENCE IF NOT EXISTS admin_id_seq")
    op.execute(
        "SELECT setval('admin_id_seq', "
        "GREATEST(COALESCE((SELECT MAX(id) FROM admin), 0) + 1, 1), false)"
    )
    op.execute("UPDATE admin SET id = nextval('admin_id_seq') WHERE id IS NULL")
    op.alter_column("admin", "id", existing_type=sa.Integer(), nullable=False)
    op.create_index("uq_admin_id", "admin", ["id"], unique=True)
    op.alter_column(
        "admin",
        "password",
        existing_type=sa.String(length=128),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "admin",
        "password",
        existing_type=sa.Text(),
        type_=sa.String(length=128),
        existing_nullable=True,
    )
    op.drop_index("uq_admin_id", table_name="admin")
    op.alter_column("admin", "id", existing_type=sa.Integer(), nullable=True)
    op.execute("DROP SEQUENCE IF EXISTS admin_id_seq")
    op.drop_column("parking_lot", "currency")

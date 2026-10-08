"""Create the initial ParkMate schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-08
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_type_enum = postgresql.ENUM("U", "M", "A", name="user_type_enum", create_type=False)
lot_available_enum = postgresql.ENUM(
    "ACTIVE", "PENDING", "BLOCK", "DELETE", name="lot_available", create_type=False
)
floor_available_enum = postgresql.ENUM(
    "ACTIVE", "PENDING", "BLOCK", "DELETE", name="floor_available", create_type=False
)
spot_available_enum = postgresql.ENUM(
    "ACTIVE", "PENDING", "BLOCK", "DELETE", name="spot_available", create_type=False
)
spot_booking_status_enum = postgresql.ENUM(
    "COMPLETED", "ACTIVE", "A", "O", name="spot_booking_status", create_type=False
)
booking_status_enum = postgresql.ENUM(
    "COMPLETED", "ACTIVE", "A", "O", name="booking_status_enum", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    bind = op.get_bind()
    for enum_type in (
        user_type_enum,
        lot_available_enum,
        floor_available_enum,
        spot_available_enum,
        spot_booking_status_enum,
        booking_status_enum,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "admin",
        sa.Column("id", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("username"),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password", sa.Text(), nullable=False),
        sa.Column("phone_no", sa.String(length=20), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=128), nullable=False),
        sa.Column("address", sa.String(length=200), nullable=False),
        sa.Column("pincode", sa.String(length=10), nullable=False),
        sa.Column("current_location", Geography(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("location_permission_granted", sa.Boolean(), nullable=True),
        sa.Column("last_location_update", sa.DateTime(), nullable=True),
        sa.Column("user_type", user_type_enum, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone_no"),
        sa.UniqueConstraint("email", "phone_no", name="unique_user"),
    )
    op.create_index("idx_user_location", "user", ["current_location"], unique=False, postgresql_using="gist")
    op.create_table(
        "parking_lot",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("location_name", sa.String(), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("pincode", sa.String(length=20), nullable=False),
        sa.Column("location_coordinates", Geography(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("available", lot_available_enum, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parking_lot_user_id", "parking_lot", ["user_id"], unique=False)
    op.create_index("idx_lot_location", "parking_lot", ["location_coordinates"], unique=False, postgresql_using="gist")
    op.create_table(
        "floor",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parking_lot_id", sa.Integer(), nullable=False),
        sa.Column("floor_id", sa.Integer(), nullable=False),
        sa.Column("available", floor_available_enum, nullable=False),
        sa.ForeignKeyConstraint(["parking_lot_id"], ["parking_lot.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("parking_lot_id", "floor_id", name="unique_floor_per_lot"),
    )
    op.create_table(
        "parking_spot",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("floor_id", sa.Integer(), nullable=False),
        sa.Column("spot_id", sa.Integer(), nullable=False),
        sa.Column("status", spot_booking_status_enum, nullable=False),
        sa.Column("available", spot_available_enum, nullable=False),
        sa.ForeignKeyConstraint(["floor_id"], ["floor.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("floor_id", "spot_id", name="unique_spot_per_floor"),
    )
    op.create_table(
        "parking_booking",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("spot_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("parking_timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("parking_timezone", sa.String(length=64), nullable=False),
        sa.Column("leaving_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cost_per_unit", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", booking_status_enum, nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.ForeignKeyConstraint(["spot_id"], ["parking_spot.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
def downgrade() -> None:
    op.drop_table("parking_booking")
    op.drop_table("parking_spot")
    op.drop_table("floor")
    op.drop_index("idx_lot_location", table_name="parking_lot")
    op.drop_index("ix_parking_lot_user_id", table_name="parking_lot")
    op.drop_table("parking_lot")
    op.drop_index("idx_user_location", table_name="user")
    op.drop_table("user")
    op.drop_table("admin")
    for enum_type in (
        booking_status_enum,
        spot_booking_status_enum,
        spot_available_enum,
        floor_available_enum,
        lot_available_enum,
        user_type_enum,
    ):
        enum_type.drop(op.get_bind(), checkfirst=True)

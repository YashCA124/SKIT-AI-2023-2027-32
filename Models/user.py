from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, Enum, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base import Base
from user_type import UserType


def enum_values(enum_cls):
    return [e.value for e in enum_cls]


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    password: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    phone_no: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    country: Mapped[str] = mapped_column(
        String(2),
        nullable=False
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    state: Mapped[str] = mapped_column(
        String(128),
        nullable=False
    )

    address: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    pincode: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    current_location = mapped_column(
        Geography(
            geometry_type="POINT",
            srid=4326
        ),
        nullable=True
    )

    location_permission_granted: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        default=None
    )

    last_location_update: Mapped[DateTime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    user_type: Mapped[UserType] = mapped_column(
        Enum(
            UserType,
            name="user_type_enum",
            values_callable=enum_values
        ),
        nullable=False
    )

    parking_lots: Mapped[list["ParkingLot"]] = relationship(
        "ParkingLot",
        back_populates="owner",
        cascade="all, delete"
    )

    __table_args__ = (
        UniqueConstraint(
            "email",
            "phone_no",
            name="unique_user"
        ),
        Index(
            "idx_user_location",
            "current_location",
            postgresql_using="gist"
        ),
    )
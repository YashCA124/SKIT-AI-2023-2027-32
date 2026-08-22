from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base import Base
from available_status import AvailableStatus


def enum_values(enum_cls):
    return [e.value for e in enum_cls]


class ParkingLot(Base):
    __tablename__ = "parking_lot"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    location_name: Mapped[str] = mapped_column(
        String,
        nullable=False
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
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
        String(100),
        nullable=False
    )

    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    pincode: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    location_coordinates = mapped_column(
        Geography(
            geometry_type="POINT",
            srid=4326
        ),
        nullable=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    available: Mapped[AvailableStatus] = mapped_column(
        Enum(
            AvailableStatus,
            name="lot_available",
            values_callable=enum_values
        ),
        nullable=False,
        default=AvailableStatus.ACTIVE
    )

    floors: Mapped[list["Floor"]] = relationship(
        "Floor",
        back_populates="parking_lot",
        cascade="all, delete"
    )

    __table_args__ = (
        Index(
            "idx_lot_location",
            "location_coordinates",
            postgresql_using="gist"
        ),
    )

    @property
    def full_address(self) -> str:
        return (
            f"{self.location_name}, "
            f"{self.address}, "
            f"{self.city}, "
            f"{self.state}, "
            f"{self.country}, "
            f"{self.pincode}"
        )
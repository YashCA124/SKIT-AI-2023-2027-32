from sqlalchemy import Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from base import Base
from booking_status import BookingStatus
from available_status import AvailableStatus


def enum_values(enum_cls):
    return [e.value for e in enum_cls]


class ParkingSpot(Base):
    __tablename__ = "parking_spot"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    floor_id: Mapped[int] = mapped_column(
        ForeignKey("floor.id"),
        nullable=False
    )

    spot_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    status: Mapped[BookingStatus] = mapped_column(
        Enum(
            BookingStatus,
            name="spot_booking_status",
            values_callable=enum_values
        ),
        nullable=False,
        default=BookingStatus.SPOT_AVAILABLE
    )

    available: Mapped[AvailableStatus] = mapped_column(
        Enum(
            AvailableStatus,
            name="spot_available",
            values_callable=enum_values
        ),
        nullable=False,
        default=AvailableStatus.ACTIVE
    )

    floor: Mapped["Floor"] = relationship(
        "Floor",
        back_populates="spots"
    )

    __table_args__ = (
        UniqueConstraint(
            "floor_id",
            "spot_id",
            name="unique_spot_per_floor"
        ),
    )

    @property
    def full_spot_id(self) -> str:
        return f"{self.floor.label}-{self.spot_id}"
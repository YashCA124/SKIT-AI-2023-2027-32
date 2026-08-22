from sqlalchemy import Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from base import Base
from available_status import AvailableStatus
from parking_spot import ParkingSpot


def enum_values(enum_cls):
    return [e.value for e in enum_cls]


class Floor(Base):
    __tablename__ = "floor"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    parking_lot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_lot.id"),
        nullable=False
    )

    floor_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    available: Mapped[AvailableStatus] = mapped_column(
        Enum(
            AvailableStatus,
            name="floor_available",
            values_callable=enum_values
        ),
        nullable=False,
        default=AvailableStatus.ACTIVE
    )

    spots: Mapped[list["ParkingSpot"]] = relationship(
        "ParkingSpot",
        back_populates="floor",
        cascade="all, delete-orphan",
        lazy="select"
    )

    __table_args__ = (
        UniqueConstraint(
            "parking_lot_id",
            "floor_id",
            name="unique_floor_per_lot"
        ),
    )

    @property
    def label(self) -> str:
        if self.floor_id < 0:
            return f"B{abs(self.floor_id)}"
        elif self.floor_id == 0:
            return "G"
        return f"F{self.floor_id}"

    @property
    def total_spot_count(self) -> int:
        return len(self.spots)
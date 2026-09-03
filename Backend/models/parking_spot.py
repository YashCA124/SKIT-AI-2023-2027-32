from core.db import Base
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Enum as SQLEnum
from booking_status import BookingStatus
from available_status import AvailableStatus

def enum_values(enum_cls):
    return [e.value for e in enum_cls]

class ParkingSpot(Base):
    __tablename__ = 'parking_spot'
    id = Column(Integer, primary_key=True, autoincrement=True)
    floor_id = Column(Integer, ForeignKey('floor.id'), nullable=False)
    spot_id = Column(Integer, nullable=False)
    status = Column(
        SQLEnum(
            BookingStatus,
            name="spot_booking_status",
            values_callable=enum_values
        ),
        nullable=False,
        default=BookingStatus.SPOT_AVAILABLE
    )

    available = Column(
        SQLEnum(
            AvailableStatus,
            name="spot_available",
            values_callable=enum_values
        ),
        nullable=False,
        default=AvailableStatus.ACTIVE
    )

    __table_args__ = (
        UniqueConstraint('floor_id', 'spot_id', name='unique_spot_per_floor'),
    )

    @property
    def full_spot_id(self):
        return f"{self.floor.label}-{self.spot_id}"
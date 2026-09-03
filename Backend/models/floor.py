from core.db import Base
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from available_status import AvailableStatus

def enum_values(enum_cls):
    return [e.value for e in enum_cls]

class Floor(Base):
    __tablename__ = 'floor'

    id = Column(Integer, primary_key=True, autoincrement=True)
    parking_lot_id = Column(Integer, ForeignKey('parking_lot.id'), nullable=False)
    floor_id = Column(Integer, nullable=False)  

    spots = relationship('ParkingSpot', backref='floor', cascade="all, delete-orphan", lazy=True)
    available = Column(
        SQLEnum(
            AvailableStatus,
            name="floor_available",
            values_callable=enum_values
        ),
        nullable=False,
        default=AvailableStatus.ACTIVE
    )

    __table_args__ = (
        UniqueConstraint('parking_lot_id', 'floor_id', name='unique_floor_per_lot'),
    )

    @property
    def label(self):
        if self.floor_id < 0:
            return f"B{abs(self.floor_id)}"
        elif self.floor_id == 0:
            return "G"
        return f"F{self.floor_id}"
    
    @property
    def total_spot_count(self):
        return len(self.spots)
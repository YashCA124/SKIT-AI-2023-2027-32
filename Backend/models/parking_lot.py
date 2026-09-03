from core.db import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Index, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from available_status import AvailableStatus

def enum_values(enum_cls):
    return [e.value for e in enum_cls]

class ParkingLot(Base):
    __tablename__ = 'parking_lot'
    id = Column(Integer, primary_key=True, autoincrement=True)
    location_name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    country = Column(String(2), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    pincode = Column(String(20), nullable=False)
    floors = relationship('Floor', backref='parking_lot', cascade="all, delete", lazy=True)
    location_coordinates = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    available = Column(
        SQLEnum(
            AvailableStatus,
            name="lot_available",
            values_callable=enum_values
        ),
        nullable=False,
        default=AvailableStatus.ACTIVE
    )

    __table_args__ = (
        Index('idx_lot_location', 'location_coordinates', postgresql_using='gist'),
    )

    @property
    def full_address(self):
        return f"{self.location_name}, {self.address}, {self.city}, {self.state}, {self.country}, {self.pincode}"
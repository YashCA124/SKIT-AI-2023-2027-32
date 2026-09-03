from core.db import Base
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from user_type import UserType

def enum_values(enum_cls):
    return [e.value for e in enum_cls]

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(Text, nullable=False)
    phone_no = Column(String(20), unique=True, nullable=False)
    country = Column(String(2), nullable=False)  
    city = Column(String(100), nullable=False)
    state = Column(String(128), nullable=False)
    address = Column(String(200), nullable=False)
    pincode = Column(String(10), nullable=False)
    current_location = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)
    location_permission_granted = Column(Boolean, default=None)
    last_location_update = Column(DateTime, nullable=True)
    user_type = Column(
        SQLEnum(
            UserType,
            name="user_type_enum",
            values_callable=enum_values
        ),
        nullable=False
    )
    parking_lots = relationship("ParkingLot", backref="owner", lazy=True, cascade="all, delete")

    __table_args__ = (
        UniqueConstraint('email', 'phone_no', name='unique_user'),
        Index('idx_user_location', 'current_location', postgresql_using='gist')
    )
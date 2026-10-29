from core.db import Base
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Payment(Base):
    __tablename__ = "payment"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'SUCCEEDED', 'FAILED')",
            name="ck_payment_status",
        ),
    )

    id = Column(Integer, primary_key=True)
    booking_id = Column(
        Integer,
        ForeignKey("parking_booking.id"),
        nullable=False,
        unique=True,
    )
    provider = Column(String(16), nullable=False, default="DEMO")
    transaction_reference = Column(String(64), nullable=True, unique=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(16), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    booking = relationship("ParkingBooking", back_populates="payment")

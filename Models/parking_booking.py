from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from zoneinfo import ZoneInfo

from base import Base
from booking_status import BookingStatus
from currency import currency


def enum_values(enum_cls):
    return [e.value for e in enum_cls]


class ParkingBooking(Base):
    __tablename__ = "parking_booking"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    spot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_spot.id"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"),
        nullable=False
    )

    parking_timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    parking_timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="UTC"
    )

    leaving_timestamp: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    cost_per_unit: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    status: Mapped[BookingStatus] = mapped_column(
        Enum(
            BookingStatus,
            name="booking_status_enum",
            values_callable=enum_values
        ),
        nullable=False,
        default=BookingStatus.BOOKING_ACTIVE
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False
    )

    exchange_rate: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False
    )

    spot: Mapped["ParkingSpot"] = relationship(
        "ParkingSpot"
    )

    user: Mapped["User"] = relationship(
        "User"
    )

    @property
    def get_local_parking_timestamp(self):
        if self.parking_timestamp:
            return self.parking_timestamp.astimezone(
                ZoneInfo(self.parking_timezone)
            ).strftime("%Y-%m-%d %H:%M:%S")

        return None

    @property
    def get_local_leaving_timestamp(self):
        if self.leaving_timestamp:
            return self.leaving_timestamp.astimezone(
                ZoneInfo(self.parking_timezone)
            ).strftime("%Y-%m-%d %H:%M:%S")

        return None

    @property
    def get_lot_name(self):
        if self.spot.floor.parking_lot.full_address:
            return self.spot.floor.parking_lot.full_address

        return None

    @property
    def get_lot_currency(self):
        lot_country = self.spot.floor.parking_lot.country
        return currency.get(
            lot_country,
            "CURRENCY_NOT_AVAILABLE"
        )

    @property
    def get_total_hour(self):
        if self.leaving_timestamp and self.parking_timestamp:
            delta = self.leaving_timestamp - self.parking_timestamp
            hours = delta.total_seconds() / 3600

            return round(hours, 2)

        return None

    @property
    def get_total_cost(self):
        if self.leaving_timestamp:
            hours = self.get_total_hour

            if hours is None:
                return None

            base_cost = float(hours) * float(self.cost_per_unit)
            total_cost = base_cost * 1.05

            return round(total_cost, 2)

        return None
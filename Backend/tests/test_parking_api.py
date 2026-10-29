import os
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://test:test@localhost:5432/parkmate",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-not-for-deployment")

from fastapi import HTTPException

from models import (
    AvailableStatus,
    BookingStatus,
    Floor,
    ParkingBooking,
    ParkingLot,
    ParkingSpot,
    Payment,
    UserType,
)
from routers.parking_api import (
    create_booking,
    end_booking,
    require_role,
    simulate_demo_payment,
)
from schemas.parking import BookingCreate, DemoPaymentSimulation, LotCreate


def parking_objects(spot_status=BookingStatus.SPOT_AVAILABLE):
    lot = ParkingLot(
        id=3,
        location_name="Actual Test Garage",
        price=Decimal("25.00"),
        currency="INR",
        country="IN",
        city="Jaipur",
        state="Rajasthan",
        address="1 Test Road",
        pincode="302001",
        user_id=7,
        available=AvailableStatus.ACTIVE,
    )
    floor = Floor(id=2, parking_lot_id=3, floor_id=0, available=AvailableStatus.ACTIVE)
    floor.parking_lot = lot
    spot = ParkingSpot(
        id=9,
        floor_id=2,
        spot_id=1,
        status=spot_status,
        available=AvailableStatus.ACTIVE,
    )
    spot.floor = floor
    floor.spots = [spot]
    lot.floors = [floor]
    return lot, floor, spot


class ParkingApiTests(unittest.TestCase):
    def test_live_routes_are_mounted(self):
        from main import app

        paths = set(app.openapi()["paths"])
        self.assertIn("/api/parking/lots", paths)
        self.assertIn("/api/bookings", paths)
        self.assertIn("/api/payments/{payment_id}/simulate", paths)
        self.assertIn("/api/merchant/lots", paths)
        self.assertIn("/api/admin/users", paths)

    def test_role_dependency_denies_the_wrong_role(self):
        dependency = require_role(UserType.PARKING_MERCHANT)
        with self.assertRaises(HTTPException) as raised:
            dependency({"role": UserType.PARKING_USER.value})
        self.assertEqual(raised.exception.status_code, 403)

    def test_booking_reserves_a_real_available_space(self):
        _, _, spot = parking_objects()
        db = MagicMock()
        db.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = spot
        db.refresh.side_effect = lambda booking: setattr(booking, "spot", spot)

        result = create_booking(
            BookingCreate(spot_id=spot.id),
            {"id": 17, "role": UserType.PARKING_USER.value},
            db,
        )

        booking = db.add.call_args.args[0]
        self.assertEqual(result["spot_label"], "G-1")
        self.assertEqual(result["status"], BookingStatus.BOOKING_ACTIVE.value)
        self.assertEqual(booking.user_id, 17)
        self.assertEqual(spot.status, BookingStatus.SPOT_BOOKED)
        db.commit.assert_called_once()

    def test_booking_rejects_a_space_that_is_already_taken(self):
        _, _, spot = parking_objects(BookingStatus.SPOT_BOOKED)
        db = MagicMock()
        db.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = spot

        with self.assertRaises(HTTPException) as raised:
            create_booking(
                BookingCreate(spot_id=spot.id),
                {"id": 17, "role": UserType.PARKING_USER.value},
                db,
            )
        self.assertEqual(raised.exception.status_code, 409)
        db.add.assert_not_called()

    def test_ending_booking_persists_end_time_and_releases_space(self):
        _, _, spot = parking_objects(BookingStatus.SPOT_BOOKED)
        booking = ParkingBooking(
            id=12,
            spot_id=spot.id,
            user_id=17,
            parking_timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
            parking_timezone="UTC",
            cost_per_unit=Decimal("25.00"),
            status=BookingStatus.BOOKING_ACTIVE,
            currency="INR",
            exchange_rate=Decimal("1.0000"),
            spot=spot,
        )
        db = MagicMock()
        db.query.return_value.filter_by.return_value.with_for_update.return_value.first.return_value = booking

        result = end_booking(12, {"id": 17, "role": UserType.PARKING_USER.value}, db)

        self.assertEqual(result["status"], BookingStatus.BOOKING_COMPLETED.value)
        self.assertIsNotNone(booking.leaving_timestamp)
        self.assertEqual(spot.status, BookingStatus.SPOT_AVAILABLE)
        payment = db.add.call_args.args[0]
        self.assertEqual(payment.booking, booking)
        self.assertEqual(payment.status, "PENDING")
        self.assertEqual(payment.currency, "INR")
        db.commit.assert_called_once()

    def test_demo_payment_simulation_marks_payment_successful(self):
        payment = Payment(
            id=31,
            booking_id=12,
            provider="DEMO",
            amount=Decimal("26.25"),
            currency="INR",
            status="PENDING",
        )
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.with_for_update.return_value.first.return_value = payment

        result = simulate_demo_payment(
            31,
            DemoPaymentSimulation(outcome="SUCCESS"),
            {"id": 17, "role": UserType.PARKING_USER.value},
            db,
        )

        self.assertEqual(result["payment"]["status"], "SUCCEEDED")
        self.assertTrue(result["payment"]["transaction_reference"].startswith("DEMO_"))
        db.commit.assert_called_once()

    def test_demo_payment_simulation_marks_payment_failed(self):
        payment = Payment(
            id=31,
            booking_id=12,
            provider="DEMO",
            amount=Decimal("26.25"),
            currency="INR",
            status="PENDING",
        )
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.with_for_update.return_value.first.return_value = payment

        result = simulate_demo_payment(
            31,
            DemoPaymentSimulation(outcome="FAILED"),
            {"id": 17, "role": UserType.PARKING_USER.value},
            db,
        )

        self.assertEqual(result["payment"]["status"], "FAILED")
        self.assertIsNone(result["payment"]["transaction_reference"])
        db.commit.assert_called_once()

    def test_demo_payment_simulation_is_disabled_in_production(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}):
            with self.assertRaises(HTTPException) as raised:
                simulate_demo_payment(
                    31,
                    DemoPaymentSimulation(outcome="SUCCESS"),
                    {"id": 17, "role": UserType.PARKING_USER.value},
                    MagicMock(),
                )

        self.assertEqual(raised.exception.status_code, 503)

    def test_lot_contract_rejects_duplicate_floor_numbers(self):
        with self.assertRaises(ValueError):
            LotCreate(
                location_name="Test Garage",
                price=20,
                currency="INR",
                country="IN",
                city="Jaipur",
                state="Rajasthan",
                address="1 Test Road",
                pincode="302001",
                latitude=26.9,
                longitude=75.8,
                floors=[{"floor_id": 0, "total_spots": 3}, {"floor_id": 0, "total_spots": 2}],
            )


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from decimal import Decimal
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/parkmate")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-not-for-deployment")

from fastapi import HTTPException

from models import AvailableStatus, ParkingLot, User, UserType
from routers.parking_api import (
    delete_admin_lot,
    delete_merchant,
    update_admin_lot,
    update_user_role,
)
from schemas._common import load_payload
from schemas.parking import AdminLotUpdate, UserRoleUpdate


class AdminControlTests(unittest.TestCase):
    def test_admin_management_routes_are_mounted(self):
        from main import app

        paths = app.openapi()["paths"]
        self.assertIn("patch", paths["/api/admin/users/{user_id}/role"])
        self.assertIn("delete", paths["/api/admin/users/{user_id}"])
        self.assertIn("patch", paths["/api/admin/parking-lots/{lot_id}/details"])
        self.assertIn("delete", paths["/api/admin/parking-lots/{lot_id}"])

    def test_role_schema_accepts_grant_and_revoke(self):
        self.assertEqual(load_payload(UserRoleUpdate, {"role": "M"}).role, "M")
        self.assertEqual(load_payload(UserRoleUpdate, {"role": "U"}).role, "U")

    def test_admin_can_reassign_and_edit_a_lot(self):
        old_owner = User(id=7, name="Old merchant")
        new_owner = User(
            id=8,
            name="New merchant",
            user_type=UserType.PARKING_MERCHANT,
        )
        lot = ParkingLot(
            id=3,
            location_name="Old Garage",
            price=Decimal("25.00"),
            currency="INR",
            country="IN",
            city="Jaipur",
            state="Rajasthan",
            address="1 Old Road",
            pincode="302001",
            user_id=old_owner.id,
            available=AvailableStatus.ACTIVE,
            owner=old_owner,
            floors=[],
        )
        db = MagicMock()
        db.get.side_effect = lambda model, _id: (
            lot if model is ParkingLot else new_owner
        )

        update_admin_lot(
            3,
            load_payload(
                AdminLotUpdate,
                {"location_name": "Updated Garage", "owner_id": new_owner.id},
            ),
            {},
            db,
        )

        self.assertEqual(lot.location_name, "Updated Garage")
        self.assertIs(lot.owner, new_owner)
        db.commit.assert_called_once()

    def test_admin_can_revoke_merchant_access(self):
        user = User(id=8, user_type=UserType.PARKING_MERCHANT)
        db = MagicMock()
        db.get.return_value = user

        result = update_user_role(
            8, load_payload(UserRoleUpdate, {"role": "U"}), {}, db
        )

        self.assertEqual(result["role"], UserType.PARKING_USER.value)
        db.commit.assert_called_once()

    def test_merchant_with_owned_lots_cannot_be_deleted(self):
        user = User(id=8, user_type=UserType.PARKING_MERCHANT)
        db = MagicMock()
        db.get.return_value = user
        db.query.return_value.filter_by.return_value.first.return_value = 3

        with self.assertRaises(HTTPException) as raised:
            delete_merchant(8, {}, db)

        self.assertEqual(raised.exception.status_code, 409)
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    def test_eligible_merchant_can_be_deleted(self):
        user = User(id=8, user_type=UserType.PARKING_MERCHANT)
        db = MagicMock()
        db.get.return_value = user
        db.query.return_value.filter_by.return_value.first.return_value = None

        result = delete_merchant(8, {}, db)

        self.assertEqual(result["id"], user.id)
        db.delete.assert_called_once_with(user)
        db.commit.assert_called_once()

    def test_lot_with_booking_history_cannot_be_deleted(self):
        lot = ParkingLot(id=3)
        db = MagicMock()
        db.get.return_value = lot
        db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = 9

        with self.assertRaises(HTTPException) as raised:
            delete_admin_lot(3, {}, db)

        self.assertEqual(raised.exception.status_code, 409)
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    def test_lot_without_booking_history_can_be_deleted(self):
        lot = ParkingLot(id=3)
        db = MagicMock()
        db.get.return_value = lot
        db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None

        result = delete_admin_lot(3, {}, db)

        self.assertEqual(result["id"], lot.id)
        db.delete.assert_called_once_with(lot)
        db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()

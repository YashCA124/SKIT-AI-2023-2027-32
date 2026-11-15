import unittest

from marshmallow import ValidationError

from models import User, UserType
from schemas import UserCreate, UserSchema


class UserSchemaTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "name": "  Jane Doe  ",
            "email": "jane.doe@example.com",
            "password": "correct horse battery staple 73!",
            "country": "India",
            "phone_no": "+919876543210",
            "state": "Rajasthan",
            "city": "Jaipur",
            "address": "1 Test Road",
            "pincode": "302001",
            "user_type": "U",
            "location_permission_granted": False,
        }

    def test_load_normalizes_data_and_builds_user(self):
        user = UserCreate().load(self.payload)

        self.assertIsInstance(user, User)
        self.assertEqual(user.name, "Jane Doe")
        self.assertEqual(user.country, "IN")
        self.assertEqual(user.state, "rajasthan")
        self.assertEqual(user.city, "jaipur")
        self.assertEqual(user.user_type, UserType.PARKING_USER)
        self.assertEqual(user.password, self.payload["password"])

    def test_location_permission_requires_valid_coordinates(self):
        payload = {
            **self.payload,
            "location_permission_granted": True,
            "latitude": 91,
            "longitude": 181,
        }

        with self.assertRaises(ValidationError) as raised:
            UserCreate().load(payload)

        self.assertIn("latitude", raised.exception.messages)
        self.assertIn("longitude", raised.exception.messages)

    def test_password_and_phone_validation_are_preserved(self):
        weak_password = {**self.payload, "password": "password"}
        with self.assertRaises(ValidationError) as raised:
            UserCreate().load(weak_password)
        self.assertIn("password", raised.exception.messages)

        invalid_phone = {**self.payload, "phone_no": "not a phone"}
        with self.assertRaises(ValidationError) as raised:
            UserCreate().load(invalid_phone)
        self.assertIn("phone_no", raised.exception.messages)

    def test_dump_does_not_expose_password(self):
        user = UserCreate().load(self.payload)
        user.id = 12

        serialized = UserSchema().dump(user)

        self.assertEqual(serialized["id"], 12)
        self.assertEqual(serialized["user_type"], "U")
        self.assertNotIn("password", serialized)


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://parkmate:test-only@localhost:5432/parkmate",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-not-for-deployment")

import main
from models import UserType
from routers.auth import registration
from redis.exceptions import RedisError
from schemas.auth import RegistrationRequest
from sqlalchemy.exc import SQLAlchemyError


class HealthContractTests(unittest.TestCase):
    def test_health_and_ready_routes_are_defined(self):
        source = (BACKEND_ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn('@app.get("/health")', source)
        self.assertIn('@app.get("/ready")', source)
        self.assertIn('"status": "ok"', source)

    @patch("main.redis_client.ping", return_value=True)
    @patch("main.engine.connect")
    def test_readiness_is_healthy_when_database_and_redis_respond(self, connect, redis_ping):
        connection = MagicMock()
        connect.return_value.__enter__.return_value = connection

        response = main.readiness_check()
        body = json.loads(response.body)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["status"], "ready")
        self.assertTrue(body["database_connected"])
        self.assertTrue(body["redis_connected"])
        connection.execute.assert_called_once()
        redis_ping.assert_called_once()

    @patch("main.redis_client.ping", side_effect=RedisError("redis unavailable"))
    @patch("main.engine.connect", side_effect=SQLAlchemyError("database unavailable"))
    def test_readiness_is_degraded_when_dependencies_fail(self, connect, redis_ping):
        with self.assertLogs("main", level="WARNING"):
            response = main.readiness_check()
        body = json.loads(response.body)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(body["status"], "degraded")
        self.assertFalse(body["database_connected"])
        self.assertFalse(body["redis_connected"])

    def test_backend_startup_rejects_missing_jwt_secret(self):
        environment = os.environ.copy()
        environment.pop("JWT_SECRET_KEY", None)
        environment["PYTHONPATH"] = str(BACKEND_ROOT)
        environment["DATABASE_URL"] = (
            "postgresql+psycopg2://parkmate:test-only@localhost:5432/parkmate"
        )

        result = subprocess.run(
            [sys.executable, "-c", "import main"],
            cwd=BACKEND_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("JWT_SECRET_KEY must be set", result.stderr)

    def test_registration_populates_required_legacy_user_fields(self):
        db = MagicMock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        db.refresh.side_effect = lambda user: setattr(user, "id", 101)
        payload = RegistrationRequest(
            name="Smoke Test",
            email="smoke@example.com",
            phone_no="9991234567",
            password="test-password",
            city="Jaipur",
            state="Rajasthan",
            country="IN",
            location_permission_granted=True,
            latitude=26.9124,
            longitude=75.7873,
        )

        result = registration(payload, db)
        created_user = db.add.call_args.args[0]

        self.assertEqual(created_user.address, "")
        self.assertEqual(created_user.pincode, "")
        self.assertEqual(created_user.user_type, UserType.PARKING_USER)
        self.assertEqual(result["user"]["id"], 101)


class DockerContractTests(unittest.TestCase):
    def test_service_dockerfiles_exist(self):
        files = [
            "Backend/Dockerfile",
            "frontend/Dockerfile",
            "ml/Dockerfile",
            "devops/redis/Dockerfile",
            "docker-compose.yml",
            ".github/workflows/ci.yml",
        ]
        missing = [path for path in files if not (REPO_ROOT / path).is_file()]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()

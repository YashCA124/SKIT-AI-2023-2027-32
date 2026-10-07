import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


class HealthContractTests(unittest.TestCase):
    def test_health_and_ready_routes_are_defined(self):
        source = (BACKEND_ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn('@app.get("/health")', source)
        self.assertIn('@app.get("/ready")', source)
        self.assertIn('"status": "ok"', source)


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

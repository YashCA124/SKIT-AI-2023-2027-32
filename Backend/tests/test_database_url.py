import unittest

from core.database_url import get_database_url


class DatabaseUrlTests(unittest.TestCase):
    def test_normalizes_common_postgres_alias(self):
        url = get_database_url("postgres://parkmate:secret@db.example:5432/parkmate")

        self.assertEqual(url.drivername, "postgresql+psycopg2")
        self.assertEqual(url.username, "parkmate")
        self.assertEqual(url.password, "secret")
        self.assertEqual(url.host, "db.example")
        self.assertEqual(url.database, "parkmate")

    def test_normalizes_standard_postgresql_url(self):
        url = get_database_url("postgresql://parkmate:secret@localhost/parkmate")

        self.assertEqual(url.drivername, "postgresql+psycopg2")
        self.assertEqual(url.host, "localhost")

    def test_preserves_percent_encoded_password(self):
        url = get_database_url("postgres://parkmate:p%40ss%3Aword@localhost/parkmate")

        self.assertEqual(url.password, "p@ss:word")

    def test_rejects_non_postgresql_url(self):
        with self.assertRaisesRegex(ValueError, "PostgreSQL"):
            get_database_url("mysql://localhost/parkmate")

    def test_rejects_empty_url(self):
        with self.assertRaisesRegex(RuntimeError, "DATABASE_URL"):
            get_database_url("  ")


if __name__ == "__main__":
    unittest.main()

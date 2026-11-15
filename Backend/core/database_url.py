import os

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


def get_database_url(value: str | None = None) -> URL:
    database_url = (value if value is not None else os.getenv("DATABASE_URL", "")).strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set before starting the backend.")

    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg2://" + database_url[len("postgres://") :]
    elif database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg2://" + database_url[len("postgresql://") :]

    try:
        url = make_url(database_url)
    except ArgumentError as exc:
        raise ValueError(
            "DATABASE_URL must be a valid PostgreSQL SQLAlchemy URL."
        ) from exc

    if url.drivername != "postgresql+psycopg2":
        raise ValueError(
            "DATABASE_URL must use PostgreSQL with the psycopg2 driver "
            "(postgresql:// or postgres://)."
        )
    return url

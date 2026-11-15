from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from core.database_url import get_database_url

DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"connect_timeout": 3},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

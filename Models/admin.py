from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from base import Base

class Admin(Base):
    __tablename__ = "admin"

    id: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str] = mapped_column(String(100), primary_key=True)
    password: Mapped[str | None] = mapped_column(String(128), nullable=True)
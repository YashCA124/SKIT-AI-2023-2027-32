from core.db import Base
from sqlalchemy import Column, Index, Integer, String, Text

class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, nullable=False)
    username = Column(String(100), primary_key=True)
    password = Column(Text, nullable=True)

    __table_args__ = (Index("uq_admin_id", "id", unique=True),)
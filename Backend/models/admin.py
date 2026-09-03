from core.db import Base
from sqlalchemy import Column, Integer, String

class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer)
    username = Column(String(100), primary_key=True)
    password = Column(String(128), nullable=True)
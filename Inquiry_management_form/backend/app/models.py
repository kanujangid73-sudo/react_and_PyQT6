from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    number = Column(String, nullable=False)
    company = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    msg = Column(String, nullable=False)
    status = Column(String, default="Pending")
    purpose = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
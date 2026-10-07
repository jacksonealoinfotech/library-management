from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    admission_number = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(150), index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(30), nullable=False)
    department = Column(String(100), nullable=False)
    course = Column(String(100), nullable=False)
    year = Column(String(20), nullable=False)
    address = Column(Text, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    registration_date = Column(Date, default=date.today, nullable=False)
    status = Column(String(20), default="Active", nullable=False)  # Active / Inactive
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.full_name}', adm='{self.admission_number}')>"

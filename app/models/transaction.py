from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    issue_date = Column(Date, default=date.today, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)
    status = Column(String(20), default="Issued", nullable=False)  # Issued, Returned, Overdue
    overdue_days = Column(Integer, default=0, nullable=False)
    fine_amount = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    book = relationship("Book", back_populates="transactions")
    student = relationship("Student", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, book_id={self.book_id}, student_id={self.student_id}, status='{self.status}')>"

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(30), unique=True, index=True, nullable=False)
    title = Column(String(200), index=True, nullable=False)
    author = Column(String(150), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    publisher = Column(String(150), nullable=True)
    publication_year = Column(Integer, nullable=True)
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)
    shelf_number = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', isbn='{self.isbn}')>"

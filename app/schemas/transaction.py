from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class IssueCreate(BaseModel):
    book_id: int = Field(..., gt=0)
    student_id: int = Field(..., gt=0)
    issue_date: date = Field(default_factory=date.today)
    due_date: date

class ReturnRequest(BaseModel):
    transaction_id: int = Field(..., gt=0)

class TransactionOut(BaseModel):
    id: int
    book_id: int
    student_id: int
    issue_date: date
    due_date: date
    return_date: Optional[date] = None
    status: str
    overdue_days: int
    fine_amount: float
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

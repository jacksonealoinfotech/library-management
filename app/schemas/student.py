from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class StudentBase(BaseModel):
    admission_number: str = Field(..., min_length=2, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=150)
    email: str = Field(..., pattern=r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$")
    phone: str = Field(..., min_length=7, max_length=30)
    department: str = Field(..., min_length=2, max_length=100)
    course: str = Field(..., min_length=2, max_length=100)
    year: str = Field(..., min_length=1, max_length=20)
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    status: str = Field("Active", pattern="^(Active|Inactive)$")

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int
    registration_date: date
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

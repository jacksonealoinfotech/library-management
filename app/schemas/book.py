from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator

class BookBase(BaseModel):
    isbn: str = Field(..., min_length=3, max_length=30, description="International Standard Book Number")
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=150)
    category: str = Field(..., min_length=1, max_length=100)
    publisher: Optional[str] = Field(None, max_length=150)
    publication_year: Optional[int] = Field(None, ge=1000, le=2100)
    total_copies: int = Field(..., gt=0, description="Total physical copies owned")
    available_copies: Optional[int] = Field(None, ge=0, description="Currently available copies")
    shelf_number: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_copies(self):
        # Default available_copies to total_copies if not provided
        if self.available_copies is None:
            self.available_copies = self.total_copies
        if self.available_copies > self.total_copies:
            raise ValueError("Available copies cannot exceed total copies")
        return self

class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    pass

class BookOut(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

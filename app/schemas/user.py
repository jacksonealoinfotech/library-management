from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.\+\-]+@[a-zA-Z0-9\.\-]+\.[a-zA-Z]{2,}$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

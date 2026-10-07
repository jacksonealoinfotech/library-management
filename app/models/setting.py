from sqlalchemy import Column, Integer, String
from app.database import Base

class SystemSetting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<SystemSetting(key='{self.key}', value='{self.value}')>"

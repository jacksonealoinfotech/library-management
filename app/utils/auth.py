from typing import Optional
import bcrypt
from fastapi import Request, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

class UnauthenticatedException(Exception):
    """Raised when an unauthenticated user attempts to access a protected page."""
    def __init__(self, message: str = "Please log in to access this page."):
        self.message = message
        super().__init__(message)


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    # Bcrypt truncates at 72 bytes; enforce safe UTF-8 byte length
    pw_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Retrieve currently logged in user from session if present."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Invalid or deleted user session
        request.session.clear()
        return None
    return user


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """FastAPI dependency to enforce authentication on protected endpoints."""
    user = get_current_user(request, db)
    if not user:
        raise UnauthenticatedException()
    return user

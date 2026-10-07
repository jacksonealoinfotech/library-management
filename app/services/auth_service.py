from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.utils.auth import hash_password, verify_password

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user by username and plain text password."""
    user = db.query(User).filter(User.username == username.strip()).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def ensure_admin_user(db: Session) -> User:
    """Ensure the default administrator user exists in the database."""
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        hashed = hash_password("admin123")
        admin = User(
            username="admin",
            email="admin@library.edu",
            password_hash=hashed
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin


def update_admin_password(db: Session, user_id: int, current_password: str, new_password: str) -> bool:
    """Update user password after validating current password."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    if not verify_password(current_password, user.password_hash):
        return False
    user.password_hash = hash_password(new_password)
    db.commit()
    return True

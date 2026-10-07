from sqlalchemy.orm import Session
from app.config import settings
from app.models.setting import SystemSetting

DEFAULT_SETTINGS = {
    "library_name": (settings.LIBRARY_NAME, "Name of the library displayed across the application"),
    "max_books_per_student": (str(settings.MAX_BOOKS_PER_STUDENT), "Maximum number of books an active student can hold simultaneously"),
    "fine_per_day": (str(settings.FINE_PER_DAY), "Fine charged per day for overdue books (currency units)"),
    "default_due_days": (str(settings.DEFAULT_DUE_DAYS), "Default lending duration in days from issue date"),
}

def init_system_settings(db: Session) -> None:
    """Ensure default system settings exist in the database."""
    for key, (val, desc) in DEFAULT_SETTINGS.items():
        existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if not existing:
            db.add(SystemSetting(key=key, value=val, description=desc))
    db.commit()


def get_setting_value(db: Session, key: str, fallback: str = "") -> str:
    """Retrieve setting value with fallback."""
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if row and row.value is not None:
        return row.value
    if key in DEFAULT_SETTINGS:
        return DEFAULT_SETTINGS[key][0]
    return fallback


def get_all_settings(db: Session) -> dict:
    """Retrieve all current system settings as a dictionary."""
    init_system_settings(db)
    rows = db.query(SystemSetting).all()
    res = {}
    for r in rows:
        res[r.key] = r.value
    return {
        "library_name": res.get("library_name", settings.LIBRARY_NAME),
        "max_books_per_student": int(res.get("max_books_per_student", settings.MAX_BOOKS_PER_STUDENT)),
        "fine_per_day": float(res.get("fine_per_day", settings.FINE_PER_DAY)),
        "default_due_days": int(res.get("default_due_days", settings.DEFAULT_DUE_DAYS)),
    }


def update_system_settings(
    db: Session,
    library_name: str,
    max_books_per_student: int,
    fine_per_day: float,
    default_due_days: int = 14
) -> None:
    """Update settings in the database."""
    payload = {
        "library_name": library_name.strip() or settings.LIBRARY_NAME,
        "max_books_per_student": str(max(1, max_books_per_student)),
        "fine_per_day": str(max(0.0, fine_per_day)),
        "default_due_days": str(max(1, default_due_days)),
    }
    for k, v in payload.items():
        row = db.query(SystemSetting).filter(SystemSetting.key == k).first()
        if row:
            row.value = v
        else:
            db.add(SystemSetting(key=k, value=v))
    db.commit()

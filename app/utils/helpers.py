import math
from datetime import date
from typing import List, Dict, Any, Optional
from fastapi import Request
from sqlalchemy.orm import Query

def flash(request: Request, message: str, category: str = "info") -> None:
    """Add a flash message to the current user session safely."""
    try:
        if "session" not in request.scope:
            return
        messages = request.session.get("_flashes", [])
        messages.append({"message": message, "category": category})
        request.session["_flashes"] = messages
    except Exception:
        pass


def get_flashed_messages(request: Request) -> List[Dict[str, str]]:
    """Pop and return all flash messages stored in the session safely."""
    try:
        if "session" not in request.scope:
            return []
        return request.session.pop("_flashes", [])
    except Exception:
        return []


def calculate_overdue_and_fine(
    due_date: date,
    reference_date: Optional[date] = None,
    fine_per_day: float = 5.0
) -> tuple[int, float]:
    """
    Calculate overdue days and fine amount.
    If reference_date is not provided, defaults to date.today().
    """
    if reference_date is None:
        reference_date = date.today()

    if reference_date > due_date:
        overdue_days = (reference_date - due_date).days
        fine = round(overdue_days * fine_per_day, 2)
        return overdue_days, fine
    return 0, 0.0


class Pagination:
    """Helper class to manage pagination data and controls in templates."""
    def __init__(self, items: List[Any], total: int, page: int, per_page: int):
        self.items = items
        self.total = total
        self.page = max(1, page)
        self.per_page = max(1, per_page)
        self.pages = max(1, math.ceil(total / self.per_page))
        self.has_prev = self.page > 1
        self.has_next = self.page < self.pages
        self.prev_page = self.page - 1 if self.has_prev else None
        self.next_page = self.page + 1 if self.has_next else None

    @property
    def start_index(self) -> int:
        if self.total == 0:
            return 0
        return (self.page - 1) * self.per_page + 1

    @property
    def end_index(self) -> int:
        return min(self.page * self.per_page, self.total)


def paginate_query(query: Query, page: int = 1, per_page: int = 10) -> Pagination:
    """Apply LIMIT and OFFSET to an SQLAlchemy query and return a Pagination object."""
    page = max(1, page)
    per_page = max(1, per_page)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return Pagination(items=items, total=total, page=page, per_page=per_page)

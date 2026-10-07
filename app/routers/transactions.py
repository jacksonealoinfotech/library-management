from datetime import date
from typing import Optional
from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.setting_service import get_all_settings
from app.services.transaction_service import (
    list_transactions, get_transaction_by_id, enrich_transaction_status
)
from app.templating import templates
from app.utils.auth import require_auth
from app.utils.helpers import flash

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("", response_class=HTMLResponse)
async def transactions_list(
    request: Request,
    search: str = "",
    status_filter: str = "",
    student_id: Optional[int] = None,
    book_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = 1,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """View complete transaction audit history with multi-field search and filters."""
    p_from = date.fromisoformat(from_date) if from_date and from_date.strip() else None
    p_to = date.fromisoformat(to_date) if to_date and to_date.strip() else None

    pagination = list_transactions(
        db,
        search=search,
        status_filter=status_filter,
        student_id=student_id,
        book_id=book_id,
        from_date=p_from,
        to_date=p_to,
        page=page,
        per_page=12
    )
    return templates.TemplateResponse(
        "transactions/index.html",
        {
            "request": request,
            "current_user": current_user,
            "pagination": pagination,
            "search": search,
            "status_filter": status_filter,
            "from_date": from_date or "",
            "to_date": to_date or "",
            "active_page": "transactions"
        }
    )

@router.get("/{transaction_id}", response_class=HTMLResponse)
async def transaction_detail(
    transaction_id: int,
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """View full details of an individual transaction."""
    tx = get_transaction_by_id(db, transaction_id)
    if not tx:
        flash(request, "Transaction not found.", "danger")
        return RedirectResponse(url="/transactions", status_code=status.HTTP_303_SEE_OTHER)

    settings_dict = get_all_settings(db)
    enrich_transaction_status(tx, settings_dict["fine_per_day"])

    return templates.TemplateResponse(
        "transactions/detail.html",
        {
            "request": request,
            "current_user": current_user,
            "transaction": tx,
            "active_page": "transactions"
        }
    )

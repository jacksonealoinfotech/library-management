from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.student import Student
from app.services.setting_service import get_all_settings
from app.services.transaction_service import (
    issue_book, return_book, list_issued_books, get_transaction_by_id,
    TransactionServiceError
)
from app.templating import templates
from app.utils.auth import require_auth
from app.utils.helpers import flash

router = APIRouter(tags=["Circulation"])

@router.get("/issue", response_class=HTMLResponse)
async def issue_page(
    request: Request,
    book_id: Optional[int] = None,
    student_id: Optional[int] = None,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Render the issue book page with active students and available books."""
    settings_dict = get_all_settings(db)
    default_days = settings_dict["default_due_days"]

    # Active students
    students = (
        db.query(Student)
        .filter(Student.status == "Active")
        .order_by(Student.full_name)
        .all()
    )

    # Books with at least one available copy
    books = (
        db.query(Book)
        .filter(Book.available_copies > 0)
        .order_by(Book.title)
        .all()
    )

    today = date.today()
    default_due = today + timedelta(days=default_days)

    return templates.TemplateResponse(
        "circulation/issue.html",
        {
            "request": request,
            "current_user": current_user,
            "students": students,
            "books": books,
            "selected_book_id": book_id,
            "selected_student_id": student_id,
            "issue_date": today.isoformat(),
            "due_date": default_due.isoformat(),
            "max_books": settings_dict["max_books_per_student"],
            "active_page": "issue"
        }
    )

@router.post("/issue", response_class=HTMLResponse)
async def issue_submit(
    request: Request,
    book_id: int = Form(...),
    student_id: int = Form(...),
    issue_date: str = Form(...),
    due_date: str = Form(...),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Process book issue request with comprehensive validation."""
    settings_dict = get_all_settings(db)
    default_days = settings_dict["default_due_days"]

    try:
        parsed_issue = date.fromisoformat(issue_date) if issue_date else date.today()
        parsed_due = date.fromisoformat(due_date) if due_date else (parsed_issue + timedelta(days=default_days))

        tx = issue_book(
            db=db,
            book_id=book_id,
            student_id=student_id,
            issue_date=parsed_issue,
            due_date=parsed_due
        )
        flash(request, f"Book issued successfully to {tx.student.full_name}.", "success")
        return RedirectResponse(url="/issued-books", status_code=status.HTTP_303_SEE_OTHER)

    except (ValueError, TransactionServiceError) as e:
        flash(request, str(e), "danger")
        students = db.query(Student).filter(Student.status == "Active").order_by(Student.full_name).all()
        books = db.query(Book).filter(Book.available_copies > 0).order_by(Book.title).all()
        return templates.TemplateResponse(
            "circulation/issue.html",
            {
                "request": request,
                "current_user": current_user,
                "students": students,
                "books": books,
                "selected_book_id": book_id,
                "selected_student_id": student_id,
                "issue_date": issue_date,
                "due_date": due_date,
                "max_books": settings_dict["max_books_per_student"],
                "error": str(e),
                "active_page": "issue"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.get("/issued-books", response_class=HTMLResponse)
async def issued_books_list(
    request: Request,
    search: str = "",
    overdue_only: bool = False,
    page: int = 1,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """View all currently active book issues with overdue monitoring."""
    pagination = list_issued_books(
        db, search=search, overdue_only=overdue_only, page=page, per_page=10
    )
    return templates.TemplateResponse(
        "circulation/issued_books.html",
        {
            "request": request,
            "current_user": current_user,
            "pagination": pagination,
            "search": search,
            "overdue_only": overdue_only,
            "active_page": "issued_books"
        }
    )

@router.get("/return", response_class=HTMLResponse)
async def return_lookup_page(
    request: Request,
    search: str = "",
    page: int = 1,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Lookup page for returning books."""
    pagination = list_issued_books(
        db, search=search, overdue_only=False, page=page, per_page=15
    )
    return templates.TemplateResponse(
        "circulation/return.html",
        {
            "request": request,
            "current_user": current_user,
            "pagination": pagination,
            "search": search,
            "active_page": "return"
        }
    )

@router.post("/return/{transaction_id}")
async def return_submit(
    transaction_id: int,
    request: Request,
    return_date: Optional[str] = Form(None),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Process book return, calculate overdue days and fine, and restore inventory."""
    try:
        parsed_return = date.fromisoformat(return_date) if return_date and return_date.strip() else date.today()
        tx = return_book(db, transaction_id=transaction_id, return_date=parsed_return)
        
        msg = f"Book '{tx.book.title}' returned successfully."
        if tx.fine_amount > 0:
            msg += f" Overdue by {tx.overdue_days} day(s). Fine charged: ${tx.fine_amount:.2f}."
        flash(request, msg, "success")
    except (ValueError, TransactionServiceError) as e:
        flash(request, str(e), "danger")
    return RedirectResponse(url="/issued-books", status_code=status.HTTP_303_SEE_OTHER)

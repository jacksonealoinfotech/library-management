from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.book import BookCreate, BookUpdate
from app.services.book_service import (
    list_books, get_book_by_id, create_book, update_book, delete_book,
    get_all_categories, BookServiceError
)
from app.templating import templates
from app.utils.auth import require_auth
from app.utils.helpers import flash

router = APIRouter(prefix="/books", tags=["Books"])

@router.get("", response_class=HTMLResponse)
async def books_list(
    request: Request,
    search: str = "",
    category: str = "",
    availability: str = "all",
    sort_by: str = "title",
    order: str = "asc",
    page: int = 1,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """List, search, filter, and paginate books."""
    pagination = list_books(
        db, search=search, category=category, availability=availability,
        sort_by=sort_by, order=order, page=page, per_page=10
    )
    categories = get_all_categories(db)
    return templates.TemplateResponse(
        "books/index.html",
        {
            "request": request,
            "current_user": current_user,
            "pagination": pagination,
            "categories": categories,
            "search": search,
            "category": category,
            "availability": availability,
            "sort_by": sort_by,
            "order": order,
            "active_page": "books"
        }
    )

@router.get("/add", response_class=HTMLResponse)
async def book_add_page(
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Render book creation form."""
    categories = get_all_categories(db)
    return templates.TemplateResponse(
        "books/add.html",
        {
            "request": request,
            "current_user": current_user,
            "categories": categories,
            "form_data": {},
            "active_page": "books_add"
        }
    )

@router.post("/add", response_class=HTMLResponse)
async def book_add_submit(
    request: Request,
    isbn: str = Form(...),
    title: str = Form(...),
    author: str = Form(...),
    category: str = Form(...),
    publisher: Optional[str] = Form(None),
    publication_year: Optional[str] = Form(None),
    total_copies: int = Form(...),
    available_copies: Optional[str] = Form(None),
    shelf_number: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Handle new book form submission with validation."""
    raw_form = {
        "isbn": isbn, "title": title, "author": author, "category": category,
        "publisher": publisher, "publication_year": publication_year,
        "total_copies": total_copies, "available_copies": available_copies,
        "shelf_number": shelf_number, "description": description
    }
    try:
        py_year = int(publication_year) if publication_year and publication_year.strip() else None
        py_avail = int(available_copies) if available_copies and available_copies.strip() else total_copies
        
        book_in = BookCreate(
            isbn=isbn,
            title=title,
            author=author,
            category=category,
            publisher=publisher or None,
            publication_year=py_year,
            total_copies=total_copies,
            available_copies=py_avail,
            shelf_number=shelf_number or None,
            description=description or None
        )
        created = create_book(db, book_in)
        flash(request, f"Book '{created.title}' added successfully.", "success")
        return RedirectResponse(url="/books", status_code=status.HTTP_303_SEE_OTHER)
    except (ValueError, BookServiceError) as e:
        flash(request, str(e), "danger")
        categories = get_all_categories(db)
        return templates.TemplateResponse(
            "books/add.html",
            {
                "request": request,
                "current_user": current_user,
                "categories": categories,
                "form_data": raw_form,
                "error": str(e),
                "active_page": "books_add"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.get("/{book_id}", response_class=HTMLResponse)
async def book_detail(
    book_id: int,
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """View details for a specific book including active circulation and history."""
    book = get_book_by_id(db, book_id)
    if not book:
        flash(request, "Book not found.", "danger")
        return RedirectResponse(url="/books", status_code=status.HTTP_303_SEE_OTHER)

    transactions = (
        db.query(Transaction)
        .filter(Transaction.book_id == book_id)
        .order_by(Transaction.issue_date.desc())
        .limit(20)
        .all()
    )
    return templates.TemplateResponse(
        "books/detail.html",
        {
            "request": request,
            "current_user": current_user,
            "book": book,
            "transactions": transactions,
            "active_page": "books"
        }
    )

@router.get("/{book_id}/edit", response_class=HTMLResponse)
async def book_edit_page(
    book_id: int,
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Render edit form for a book."""
    book = get_book_by_id(db, book_id)
    if not book:
        flash(request, "Book not found.", "danger")
        return RedirectResponse(url="/books", status_code=status.HTTP_303_SEE_OTHER)

    categories = get_all_categories(db)
    return templates.TemplateResponse(
        "books/edit.html",
        {
            "request": request,
            "current_user": current_user,
            "book": book,
            "categories": categories,
            "active_page": "books"
        }
    )

@router.post("/{book_id}/edit", response_class=HTMLResponse)
async def book_edit_submit(
    book_id: int,
    request: Request,
    isbn: str = Form(...),
    title: str = Form(...),
    author: str = Form(...),
    category: str = Form(...),
    publisher: Optional[str] = Form(None),
    publication_year: Optional[str] = Form(None),
    total_copies: int = Form(...),
    available_copies: Optional[str] = Form(None),
    shelf_number: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Handle book edit submission with validation."""
    book = get_book_by_id(db, book_id)
    if not book:
        flash(request, "Book not found.", "danger")
        return RedirectResponse(url="/books", status_code=status.HTTP_303_SEE_OTHER)

    try:
        py_year = int(publication_year) if publication_year and publication_year.strip() else None
        py_avail = int(available_copies) if available_copies and available_copies.strip() else None

        book_in = BookUpdate(
            isbn=isbn,
            title=title,
            author=author,
            category=category,
            publisher=publisher or None,
            publication_year=py_year,
            total_copies=total_copies,
            available_copies=py_avail,
            shelf_number=shelf_number or None,
            description=description or None
        )
        updated = update_book(db, book_id, book_in)
        flash(request, f"Book '{updated.title}' updated successfully.", "success")
        return RedirectResponse(url=f"/books/{book_id}", status_code=status.HTTP_303_SEE_OTHER)
    except (ValueError, BookServiceError) as e:
        flash(request, str(e), "danger")
        categories = get_all_categories(db)
        return templates.TemplateResponse(
            "books/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "book": book,
                "categories": categories,
                "error": str(e),
                "active_page": "books"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.post("/{book_id}/delete")
async def book_delete_submit(
    book_id: int,
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete book record if no active loans exist."""
    try:
        delete_book(db, book_id)
        flash(request, "Book deleted successfully.", "success")
    except BookServiceError as e:
        flash(request, str(e), "danger")
    return RedirectResponse(url="/books", status_code=status.HTTP_303_SEE_OTHER)

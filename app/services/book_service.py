from typing import Optional, List, Tuple
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session
from app.models.book import Book
from app.models.transaction import Transaction
from app.schemas.book import BookCreate, BookUpdate
from app.utils.helpers import Pagination, paginate_query

class BookServiceError(Exception):
    pass

def get_book_by_id(db: Session, book_id: int) -> Optional[Book]:
    return db.query(Book).filter(Book.id == book_id).first()

def get_book_by_isbn(db: Session, isbn: str) -> Optional[Book]:
    return db.query(Book).filter(Book.isbn == isbn.strip()).first()

def get_all_categories(db: Session) -> List[str]:
    """Retrieve distinct categories for filtering dropdowns."""
    results = db.query(Book.category).distinct().order_by(Book.category).all()
    return [r[0] for r in results if r[0]]

def create_book(db: Session, data: BookCreate) -> Book:
    """Create a new book record with validation."""
    clean_isbn = data.isbn.strip()
    if get_book_by_isbn(db, clean_isbn):
        raise BookServiceError(f"A book with ISBN '{clean_isbn}' already exists.")

    available = data.available_copies if data.available_copies is not None else data.total_copies
    if available > data.total_copies:
        raise BookServiceError("Available copies cannot be greater than total copies.")
    if data.total_copies <= 0:
        raise BookServiceError("Total copies must be at least 1.")
    if available < 0:
        raise BookServiceError("Available copies cannot be negative.")

    book = Book(
        isbn=clean_isbn,
        title=data.title.strip(),
        author=data.author.strip(),
        category=data.category.strip(),
        publisher=data.publisher.strip() if data.publisher else None,
        publication_year=data.publication_year,
        total_copies=data.total_copies,
        available_copies=available,
        shelf_number=data.shelf_number.strip() if data.shelf_number else None,
        description=data.description.strip() if data.description else None,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book

def update_book(db: Session, book_id: int, data: BookUpdate) -> Book:
    """Update an existing book record with validation."""
    book = get_book_by_id(db, book_id)
    if not book:
        raise BookServiceError("Book not found.")

    clean_isbn = data.isbn.strip()
    existing_isbn_book = get_book_by_isbn(db, clean_isbn)
    if existing_isbn_book and existing_isbn_book.id != book.id:
        raise BookServiceError(f"Another book with ISBN '{clean_isbn}' already exists.")

    # Calculate currently issued copies
    currently_issued = book.total_copies - book.available_copies

    if data.total_copies < currently_issued:
        raise BookServiceError(
            f"Cannot reduce total copies below {currently_issued} because {currently_issued} copies are currently issued to students."
        )

    # Calculate new available copies based on total copies change
    if data.available_copies is not None:
        new_available = data.available_copies
    else:
        # Keep same issued count
        new_available = data.total_copies - currently_issued

    if new_available > data.total_copies:
        raise BookServiceError("Available copies cannot exceed total copies.")
    if new_available < 0:
        raise BookServiceError("Available copies cannot be negative.")

    book.isbn = clean_isbn
    book.title = data.title.strip()
    book.author = data.author.strip()
    book.category = data.category.strip()
    book.publisher = data.publisher.strip() if data.publisher else None
    book.publication_year = data.publication_year
    book.total_copies = data.total_copies
    book.available_copies = new_available
    book.shelf_number = data.shelf_number.strip() if data.shelf_number else None
    book.description = data.description.strip() if data.description else None

    db.commit()
    db.refresh(book)
    return book

def delete_book(db: Session, book_id: int) -> bool:
    """Delete a book record. Prevent deletion if active issues exist."""
    book = get_book_by_id(db, book_id)
    if not book:
        raise BookServiceError("Book not found.")

    active_issues = (
        db.query(Transaction)
        .filter(Transaction.book_id == book_id, Transaction.status == "Issued")
        .count()
    )
    if active_issues > 0:
        raise BookServiceError(
            f"Cannot delete book '{book.title}' because {active_issues} copy/copies are currently issued. All copies must be returned first."
        )

    db.delete(book)
    db.commit()
    return True

def list_books(
    db: Session,
    search: str = "",
    category: str = "",
    availability: str = "all",
    sort_by: str = "title",
    order: str = "asc",
    page: int = 1,
    per_page: int = 10,
) -> Pagination:
    """Search, filter, sort, and paginate books."""
    query = db.query(Book)

    # Search filter across title, author, isbn, category
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Book.title.ilike(s),
                Book.author.ilike(s),
                Book.isbn.ilike(s),
                Book.category.ilike(s),
                Book.shelf_number.ilike(s),
            )
        )

    # Category filter
    if category:
        query = query.filter(Book.category == category.strip())

    # Availability filter
    if availability == "available":
        query = query.filter(Book.available_copies > 0)
    elif availability == "unavailable":
        query = query.filter(Book.available_copies == 0)

    # Sorting
    sort_column_map = {
        "title": Book.title,
        "author": Book.author,
        "isbn": Book.isbn,
        "category": Book.category,
        "total_copies": Book.total_copies,
        "available_copies": Book.available_copies,
        "publication_year": Book.publication_year,
        "created_at": Book.created_at,
    }
    sort_col = sort_column_map.get(sort_by, Book.title)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(asc(sort_col))

    return paginate_query(query, page=page, per_page=per_page)

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session, joinedload
from app.models.book import Book
from app.models.student import Student
from app.models.transaction import Transaction
from app.services.setting_service import get_all_settings
from app.utils.helpers import Pagination, paginate_query, calculate_overdue_and_fine

class TransactionServiceError(Exception):
    pass

def get_transaction_by_id(db: Session, transaction_id: int) -> Optional[Transaction]:
    return (
        db.query(Transaction)
        .options(joinedload(Transaction.book), joinedload(Transaction.student))
        .filter(Transaction.id == transaction_id)
        .first()
    )

def enrich_transaction_status(transaction: Transaction, fine_per_day: float) -> Transaction:
    """
    Enrich an active transaction with current dynamic overdue days and estimated fine
    for display purposes without modifying committed DB values prematurely.
    """
    if transaction.status == "Issued":
        today = date.today()
        if today > transaction.due_date:
            transaction.display_status = "Overdue"
            overdue_days, est_fine = calculate_overdue_and_fine(transaction.due_date, today, fine_per_day)
            transaction.current_overdue_days = overdue_days
            transaction.current_fine_amount = est_fine
        else:
            transaction.display_status = "Issued"
            transaction.current_overdue_days = 0
            transaction.current_fine_amount = 0.0
    else:
        transaction.display_status = transaction.status
        transaction.current_overdue_days = transaction.overdue_days
        transaction.current_fine_amount = transaction.fine_amount
    return transaction

def issue_book(
    db: Session,
    book_id: int,
    student_id: int,
    issue_date: Optional[date] = None,
    due_date: Optional[date] = None,
) -> Transaction:
    """
    Issue a book to a student with all validation business rules.
    """
    settings_dict = get_all_settings(db)
    max_books = settings_dict["max_books_per_student"]
    default_due_days = settings_dict["default_due_days"]

    # 1. Validate student exists
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise TransactionServiceError("Student not found.")

    # 2. Validate student is active
    if student.status != "Active":
        raise TransactionServiceError(
            f"Unable to issue book. Student '{student.full_name}' is currently marked as Inactive."
        )

    # 3. Validate book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise TransactionServiceError("Book not found.")

    # 4. Validate book availability
    if book.available_copies <= 0:
        raise TransactionServiceError(
            f"Unable to issue this book. No copies are currently available for '{book.title}'."
        )

    # 5. Validate student book limit (< max_books active)
    active_count = (
        db.query(Transaction)
        .filter(Transaction.student_id == student_id, Transaction.status == "Issued")
        .count()
    )
    if active_count >= max_books:
        raise TransactionServiceError(
            f"Student has reached the maximum book limit ({max_books} books). Return an existing book first."
        )

    # 6. Validate student does not already have this book issued
    existing_same_book = (
        db.query(Transaction)
        .filter(
            Transaction.student_id == student_id,
            Transaction.book_id == book_id,
            Transaction.status == "Issued"
        )
        .first()
    )
    if existing_same_book:
        raise TransactionServiceError(
            f"Student '{student.full_name}' already has an active copy of '{book.title}' issued on {existing_same_book.issue_date}."
        )

    # Calculate dates
    today = issue_date or date.today()
    if not due_date:
        from datetime import timedelta
        calculated_due = today + timedelta(days=default_due_days)
    else:
        calculated_due = due_date

    if calculated_due < today:
        raise TransactionServiceError("Due date cannot be before the issue date.")

    # Decrement available copies
    book.available_copies -= 1

    # Create transaction
    tx = Transaction(
        book_id=book.id,
        student_id=student.id,
        issue_date=today,
        due_date=calculated_due,
        return_date=None,
        status="Issued",
        overdue_days=0,
        fine_amount=0.0,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

def return_book(
    db: Session,
    transaction_id: int,
    return_date: Optional[date] = None,
) -> Transaction:
    """
    Return a previously issued book, recalculating overdue days and fines.
    """
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise TransactionServiceError("Transaction not found.")

    if tx.status == "Returned":
        raise TransactionServiceError("This book has already been returned. Cannot return again.")

    settings_dict = get_all_settings(db)
    fine_per_day = settings_dict["fine_per_day"]

    actual_return_date = return_date or date.today()
    if actual_return_date < tx.issue_date:
        raise TransactionServiceError("Return date cannot be before the issue date.")

    # Calculate overdue days and fine
    overdue_days, fine_amount = calculate_overdue_and_fine(
        due_date=tx.due_date,
        reference_date=actual_return_date,
        fine_per_day=fine_per_day,
    )

    # Update transaction
    tx.return_date = actual_return_date
    tx.status = "Returned"
    tx.overdue_days = overdue_days
    tx.fine_amount = fine_amount

    # Increase book available copies (ensure never exceeds total_copies)
    book = db.query(Book).filter(Book.id == tx.book_id).first()
    if book:
        book.available_copies = min(book.total_copies, book.available_copies + 1)

    db.commit()
    db.refresh(tx)
    return tx

def list_issued_books(
    db: Session,
    search: str = "",
    overdue_only: bool = False,
    page: int = 1,
    per_page: int = 10,
) -> Pagination:
    """List currently issued books with overdue identification."""
    settings_dict = get_all_settings(db)
    fine_per_day = settings_dict["fine_per_day"]

    query = (
        db.query(Transaction)
        .join(Transaction.book)
        .join(Transaction.student)
        .options(joinedload(Transaction.book), joinedload(Transaction.student))
        .filter(Transaction.status == "Issued")
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Book.title.ilike(s),
                Book.isbn.ilike(s),
                Student.full_name.ilike(s),
                Student.admission_number.ilike(s),
            )
        )

    today = date.today()
    if overdue_only:
        query = query.filter(Transaction.due_date < today)

    # Default sort by due_date ascending so urgent/overdue are at the top
    query = query.order_by(asc(Transaction.due_date))

    paginated = paginate_query(query, page=page, per_page=per_page)
    for item in paginated.items:
        enrich_transaction_status(item, fine_per_day)

    return paginated

def list_transactions(
    db: Session,
    search: str = "",
    status_filter: str = "",
    student_id: Optional[int] = None,
    book_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = 1,
    per_page: int = 10,
) -> Pagination:
    """Comprehensive transaction history listing with multi-field filtering."""
    settings_dict = get_all_settings(db)
    fine_per_day = settings_dict["fine_per_day"]

    query = (
        db.query(Transaction)
        .join(Transaction.book)
        .join(Transaction.student)
        .options(joinedload(Transaction.book), joinedload(Transaction.student))
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Book.title.ilike(s),
                Book.isbn.ilike(s),
                Student.full_name.ilike(s),
                Student.admission_number.ilike(s),
            )
        )

    today = date.today()
    if status_filter == "Issued":
        query = query.filter(Transaction.status == "Issued", Transaction.due_date >= today)
    elif status_filter == "Overdue":
        query = query.filter(Transaction.status == "Issued", Transaction.due_date < today)
    elif status_filter == "Returned":
        query = query.filter(Transaction.status == "Returned")

    if student_id:
        query = query.filter(Transaction.student_id == student_id)

    if book_id:
        query = query.filter(Transaction.book_id == book_id)

    if from_date:
        query = query.filter(Transaction.issue_date >= from_date)

    if to_date:
        query = query.filter(Transaction.issue_date <= to_date)

    query = query.order_by(desc(Transaction.issue_date), desc(Transaction.id))

    paginated = paginate_query(query, page=page, per_page=per_page)
    for item in paginated.items:
        enrich_transaction_status(item, fine_per_day)

    return paginated

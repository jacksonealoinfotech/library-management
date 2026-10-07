from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.models.book import Book
from app.models.student import Student
from app.models.transaction import Transaction
from app.services.setting_service import get_all_settings
from app.services.transaction_service import enrich_transaction_status

def get_dashboard_statistics(db: Session) -> Dict[str, Any]:
    """Calculate all key metrics and chart datasets for the dashboard."""
    settings_dict = get_all_settings(db)
    fine_per_day = settings_dict["fine_per_day"]
    today = date.today()

    # Books metrics
    total_titles = db.query(func.count(Book.id)).scalar() or 0
    total_copies = db.query(func.sum(Book.total_copies)).scalar() or 0
    available_copies = db.query(func.sum(Book.available_copies)).scalar() or 0
    issued_copies = total_copies - available_copies
    if issued_copies < 0:
        issued_copies = 0

    # Students metrics
    total_students = db.query(func.count(Student.id)).scalar() or 0
    active_students = db.query(func.count(Student.id)).filter(Student.status == "Active").scalar() or 0

    # Circulation metrics
    total_issues = db.query(func.count(Transaction.id)).scalar() or 0
    active_issued_count = db.query(func.count(Transaction.id)).filter(Transaction.status == "Issued").scalar() or 0
    overdue_count = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.status == "Issued", Transaction.due_date < today)
        .scalar() or 0
    )
    returned_count = db.query(func.count(Transaction.id)).filter(Transaction.status == "Returned").scalar() or 0
    total_fines = db.query(func.sum(Transaction.fine_amount)).scalar() or 0.0

    # Recent transactions (latest 5)
    recent_transactions = (
        db.query(Transaction)
        .order_by(desc(Transaction.created_at))
        .limit(5)
        .all()
    )
    for tx in recent_transactions:
        enrich_transaction_status(tx, fine_per_day)

    # Activity chart data: issues per day over the last 14 days
    days_labels = []
    issues_trend = []
    returns_trend = []
    start_date = today - timedelta(days=13)
    for i in range(14):
        d = start_date + timedelta(days=i)
        days_labels.append(d.strftime("%b %d"))
        
        c_issue = db.query(func.count(Transaction.id)).filter(Transaction.issue_date == d).scalar() or 0
        issues_trend.append(c_issue)

        c_return = db.query(func.count(Transaction.id)).filter(Transaction.return_date == d).scalar() or 0
        returns_trend.append(c_return)

    # Popular books (Top 5)
    popular_query = (
        db.query(
            Book.title,
            func.count(Transaction.id).label("issue_count")
        )
        .join(Transaction, Transaction.book_id == Book.id)
        .group_by(Book.id)
        .order_by(desc("issue_count"))
        .limit(5)
        .all()
    )
    popular_labels = [p[0] for p in popular_query]
    popular_counts = [p[1] for p in popular_query]

    return {
        "total_titles": total_titles,
        "total_copies": total_copies,
        "available_copies": available_copies,
        "issued_copies": issued_copies,
        "total_students": total_students,
        "active_students": active_students,
        "total_issues": total_issues,
        "active_issued_count": active_issued_count,
        "overdue_count": overdue_count,
        "returned_count": returned_count,
        "total_fines": round(total_fines, 2),
        "recent_transactions": recent_transactions,
        "chart_activity_labels": days_labels,
        "chart_activity_issues": issues_trend,
        "chart_activity_returns": returns_trend,
        "chart_popular_labels": popular_labels,
        "chart_popular_counts": popular_counts,
    }


def get_reports_data(
    db: Session,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Generate in-depth reports data with optional date filtering."""
    settings_dict = get_all_settings(db)
    fine_per_day = settings_dict["fine_per_day"]
    today = date.today()

    # Query for filtered transactions
    tx_query = db.query(Transaction)
    if from_date:
        tx_query = tx_query.filter(Transaction.issue_date >= from_date)
    if to_date:
        tx_query = tx_query.filter(Transaction.issue_date <= to_date)

    filtered_transactions = tx_query.order_by(desc(Transaction.issue_date)).all()
    for tx in filtered_transactions:
        enrich_transaction_status(tx, fine_per_day)

    period_issues = len(filtered_transactions)
    period_returned = sum(1 for tx in filtered_transactions if tx.status == "Returned")
    period_active = sum(1 for tx in filtered_transactions if tx.status == "Issued")
    period_overdue = sum(1 for tx in filtered_transactions if tx.status == "Issued" and tx.due_date < today)
    period_fines = sum(tx.fine_amount for tx in filtered_transactions if tx.status == "Returned")

    # Global summary stats
    total_titles = db.query(func.count(Book.id)).scalar() or 0
    total_copies = db.query(func.sum(Book.total_copies)).scalar() or 0
    available_copies = db.query(func.sum(Book.available_copies)).scalar() or 0
    total_students = db.query(func.count(Student.id)).scalar() or 0
    active_students = db.query(func.count(Student.id)).filter(Student.status == "Active").scalar() or 0

    # Top most issued books in filtered period
    top_books_query = (
        db.query(
            Book.title,
            Book.isbn,
            Book.author,
            Book.category,
            func.count(Transaction.id).label("issue_count")
        )
        .join(Transaction, Transaction.book_id == Book.id)
    )
    if from_date:
        top_books_query = top_books_query.filter(Transaction.issue_date >= from_date)
    if to_date:
        top_books_query = top_books_query.filter(Transaction.issue_date <= to_date)

    top_books = (
        top_books_query.group_by(Book.id)
        .order_by(desc("issue_count"))
        .limit(10)
        .all()
    )

    # Top active students in filtered period
    top_students_query = (
        db.query(
            Student.full_name,
            Student.admission_number,
            Student.department,
            Student.course,
            func.count(Transaction.id).label("borrow_count")
        )
        .join(Transaction, Transaction.student_id == Student.id)
    )
    if from_date:
        top_students_query = top_students_query.filter(Transaction.issue_date >= from_date)
    if to_date:
        top_students_query = top_students_query.filter(Transaction.issue_date <= to_date)

    top_students = (
        top_students_query.group_by(Student.id)
        .order_by(desc("borrow_count"))
        .limit(10)
        .all()
    )

    return {
        "from_date": from_date,
        "to_date": to_date,
        "total_titles": total_titles,
        "total_copies": total_copies,
        "available_copies": available_copies,
        "total_students": total_students,
        "active_students": active_students,
        "period_issues": period_issues,
        "period_returned": period_returned,
        "period_active": period_active,
        "period_overdue": period_overdue,
        "period_fines": round(period_fines, 2),
        "top_books": top_books,
        "top_students": top_students,
        "transactions": filtered_transactions,
    }

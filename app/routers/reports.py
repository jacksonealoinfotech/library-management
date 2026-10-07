import csv
import io
from datetime import date
from typing import Optional
from fastapi import APIRouter, Request, Depends, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.report_service import get_reports_data
from app.templating import templates
from app.utils.auth import require_auth

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """View library analytics, operational reports, top books and active students."""
    p_from = date.fromisoformat(from_date) if from_date and from_date.strip() else None
    p_to = date.fromisoformat(to_date) if to_date and to_date.strip() else None

    report_data = get_reports_data(db, from_date=p_from, to_date=p_to)

    return templates.TemplateResponse(
        "reports/index.html",
        {
            "request": request,
            "current_user": current_user,
            "report": report_data,
            "from_date": from_date or "",
            "to_date": to_date or "",
            "active_page": "reports"
        }
    )

@router.get("/export")
async def export_report_csv(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Export filtered transaction records to a CSV file."""
    p_from = date.fromisoformat(from_date) if from_date and from_date.strip() else None
    p_to = date.fromisoformat(to_date) if to_date and to_date.strip() else None

    report_data = get_reports_data(db, from_date=p_from, to_date=p_to)
    transactions = report_data["transactions"]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Transaction ID",
        "Book Title",
        "ISBN",
        "Student Name",
        "Admission Number",
        "Issue Date",
        "Due Date",
        "Return Date",
        "Status",
        "Overdue Days",
        "Fine Amount ($)"
    ])

    for tx in transactions:
        writer.writerow([
            tx.id,
            tx.book.title if tx.book else "N/A",
            tx.book.isbn if tx.book else "N/A",
            tx.student.full_name if tx.student else "N/A",
            tx.student.admission_number if tx.student else "N/A",
            tx.issue_date.isoformat(),
            tx.due_date.isoformat(),
            tx.return_date.isoformat() if tx.return_date else "",
            tx.status,
            tx.overdue_days,
            f"{tx.fine_amount:.2f}"
        ])

    csv_data = output.getvalue()
    filename = f"library_report_{date.today().isoformat()}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

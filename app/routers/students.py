from datetime import date
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.student import StudentCreate, StudentUpdate
from app.services.student_service import (
    list_students, get_student_by_id, create_student, update_student, delete_student,
    get_all_departments, StudentServiceError
)
from app.templating import templates
from app.utils.auth import require_auth
from app.utils.helpers import flash

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("", response_class=HTMLResponse)
async def students_list(
    request: Request,
    search: str = "",
    department: str = "",
    student_status: str = "",
    sort_by: str = "full_name",
    order: str = "asc",
    page: int = 1,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """List, search, filter, and paginate students."""
    pagination = list_students(
        db, search=search, department=department, status=student_status,
        sort_by=sort_by, order=order, page=page, per_page=10
    )
    departments = get_all_departments(db)
    return templates.TemplateResponse(
        "students/index.html",
        {
            "request": request,
            "current_user": current_user,
            "pagination": pagination,
            "departments": departments,
            "search": search,
            "department": department,
            "status_filter": student_status,
            "sort_by": sort_by,
            "order": order,
            "active_page": "students"
        }
    )

@router.get("/add", response_class=HTMLResponse)
async def student_add_page(
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Render new student registration form."""
    departments = get_all_departments(db)
    return templates.TemplateResponse(
        "students/add.html",
        {
            "request": request,
            "current_user": current_user,
            "departments": departments,
            "form_data": {},
            "active_page": "students_add"
        }
    )

@router.post("/add", response_class=HTMLResponse)
async def student_add_submit(
    request: Request,
    admission_number: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    department: str = Form(...),
    course: str = Form(...),
    year: str = Form(...),
    address: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    status_val: str = Form("Active"),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Handle new student submission with validation."""
    raw_form = {
        "admission_number": admission_number, "full_name": full_name,
        "email": email, "phone": phone, "department": department,
        "course": course, "year": year, "address": address,
        "date_of_birth": date_of_birth, "status": status_val
    }
    try:
        dob_parsed = date.fromisoformat(date_of_birth) if date_of_birth and date_of_birth.strip() else None
        student_in = StudentCreate(
            admission_number=admission_number,
            full_name=full_name,
            email=email,
            phone=phone,
            department=department,
            course=course,
            year=year,
            address=address or None,
            date_of_birth=dob_parsed,
            status=status_val
        )
        created = create_student(db, student_in)
        flash(request, f"Student '{created.full_name}' registered successfully.", "success")
        return RedirectResponse(url="/students", status_code=status.HTTP_303_SEE_OTHER)
    except (ValueError, StudentServiceError) as e:
        flash(request, str(e), "danger")
        departments = get_all_departments(db)
        return templates.TemplateResponse(
            "students/add.html",
            {
                "request": request,
                "current_user": current_user,
                "departments": departments,
                "form_data": raw_form,
                "error": str(e),
                "active_page": "students_add"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.get("/{student_id}", response_class=HTMLResponse)
async def student_detail(
    student_id: int,
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """View details for a specific student, including loan history."""
    student = get_student_by_id(db, student_id)
    if not student:
        flash(request, "Student not found.", "danger")
        return RedirectResponse(url="/students", status_code=status.HTTP_303_SEE_OTHER)

    transactions = (
        db.query(Transaction)
        .filter(Transaction.student_id == student_id)
        .order_by(Transaction.issue_date.desc())
        .all()
    )
    active_loans = [t for t in transactions if t.status == "Issued"]

    return templates.TemplateResponse(
        "students/detail.html",
        {
            "request": request,
            "current_user": current_user,
            "student": student,
            "transactions": transactions,
            "active_loans": active_loans,
            "active_page": "students"
        }
    )

@router.get("/{student_id}/edit", response_class=HTMLResponse)
async def student_edit_page(
    student_id: int,
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Render edit form for a student."""
    student = get_student_by_id(db, student_id)
    if not student:
        flash(request, "Student not found.", "danger")
        return RedirectResponse(url="/students", status_code=status.HTTP_303_SEE_OTHER)

    departments = get_all_departments(db)
    return templates.TemplateResponse(
        "students/edit.html",
        {
            "request": request,
            "current_user": current_user,
            "student": student,
            "departments": departments,
            "active_page": "students"
        }
    )

@router.post("/{student_id}/edit", response_class=HTMLResponse)
async def student_edit_submit(
    student_id: int,
    request: Request,
    admission_number: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    department: str = Form(...),
    course: str = Form(...),
    year: str = Form(...),
    address: Optional[str] = Form(None),
    date_of_birth: Optional[str] = Form(None),
    status_val: str = Form("Active"),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Handle student edit submission."""
    student = get_student_by_id(db, student_id)
    if not student:
        flash(request, "Student not found.", "danger")
        return RedirectResponse(url="/students", status_code=status.HTTP_303_SEE_OTHER)

    try:
        dob_parsed = date.fromisoformat(date_of_birth) if date_of_birth and date_of_birth.strip() else None
        student_in = StudentUpdate(
            admission_number=admission_number,
            full_name=full_name,
            email=email,
            phone=phone,
            department=department,
            course=course,
            year=year,
            address=address or None,
            date_of_birth=dob_parsed,
            status=status_val
        )
        updated = update_student(db, student_id, student_in)
        flash(request, f"Student '{updated.full_name}' updated successfully.", "success")
        return RedirectResponse(url=f"/students/{student_id}", status_code=status.HTTP_303_SEE_OTHER)
    except (ValueError, StudentServiceError) as e:
        flash(request, str(e), "danger")
        departments = get_all_departments(db)
        return templates.TemplateResponse(
            "students/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "student": student,
                "departments": departments,
                "error": str(e),
                "active_page": "students"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.post("/{student_id}/delete")
async def student_delete_submit(
    student_id: int,
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete student record if no active loans exist."""
    try:
        delete_student(db, student_id)
        flash(request, "Student deleted successfully.", "success")
    except StudentServiceError as e:
        flash(request, str(e), "danger")
    return RedirectResponse(url="/students", status_code=status.HTTP_303_SEE_OTHER)

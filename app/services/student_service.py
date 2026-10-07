from typing import Optional, List
from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session
from app.models.student import Student
from app.models.transaction import Transaction
from app.schemas.student import StudentCreate, StudentUpdate
from app.utils.helpers import Pagination, paginate_query

class StudentServiceError(Exception):
    pass

def get_student_by_id(db: Session, student_id: int) -> Optional[Student]:
    return db.query(Student).filter(Student.id == student_id).first()

def get_student_by_admission_number(db: Session, adm: str) -> Optional[Student]:
    return db.query(Student).filter(Student.admission_number == adm.strip()).first()

def get_all_departments(db: Session) -> List[str]:
    """Retrieve distinct departments for filtering."""
    results = db.query(Student.department).distinct().order_by(Student.department).all()
    return [r[0] for r in results if r[0]]

def create_student(db: Session, data: StudentCreate) -> Student:
    """Create a new student with validation."""
    clean_adm = data.admission_number.strip()
    if get_student_by_admission_number(db, clean_adm):
        raise StudentServiceError(f"A student with Admission Number '{clean_adm}' already exists.")

    student = Student(
        admission_number=clean_adm,
        full_name=data.full_name.strip(),
        email=data.email.strip().lower(),
        phone=data.phone.strip(),
        department=data.department.strip(),
        course=data.course.strip(),
        year=data.year.strip(),
        address=data.address.strip() if data.address else None,
        date_of_birth=data.date_of_birth,
        status=data.status,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

def update_student(db: Session, student_id: int, data: StudentUpdate) -> Student:
    """Update student record with validation."""
    student = get_student_by_id(db, student_id)
    if not student:
        raise StudentServiceError("Student not found.")

    clean_adm = data.admission_number.strip()
    existing_adm = get_student_by_admission_number(db, clean_adm)
    if existing_adm and existing_adm.id != student.id:
        raise StudentServiceError(f"Another student with Admission Number '{clean_adm}' already exists.")

    # If status changed to Inactive while holding books, warn or prevent?
    # Requirement: "Inactive students must not be allowed to issue books."
    # If they currently have books, they can be made Inactive, but won't be able to issue more.
    student.admission_number = clean_adm
    student.full_name = data.full_name.strip()
    student.email = data.email.strip().lower()
    student.phone = data.phone.strip()
    student.department = data.department.strip()
    student.course = data.course.strip()
    student.year = data.year.strip()
    student.address = data.address.strip() if data.address else None
    student.date_of_birth = data.date_of_birth
    student.status = data.status

    db.commit()
    db.refresh(student)
    return student

def delete_student(db: Session, student_id: int) -> bool:
    """Delete a student record. Cannot delete if holding issued books."""
    student = get_student_by_id(db, student_id)
    if not student:
        raise StudentServiceError("Student not found.")

    active_issues = (
        db.query(Transaction)
        .filter(Transaction.student_id == student_id, Transaction.status == "Issued")
        .count()
    )
    if active_issues > 0:
        raise StudentServiceError(
            f"Cannot delete student '{student.full_name}' because they currently have {active_issues} unreturned book(s). Return all books first."
        )

    db.delete(student)
    db.commit()
    return True

def list_students(
    db: Session,
    search: str = "",
    department: str = "",
    status: str = "",
    sort_by: str = "full_name",
    order: str = "asc",
    page: int = 1,
    per_page: int = 10,
) -> Pagination:
    """Search, filter, sort, and paginate students."""
    query = db.query(Student)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Student.full_name.ilike(s),
                Student.admission_number.ilike(s),
                Student.email.ilike(s),
                Student.phone.ilike(s),
                Student.department.ilike(s),
                Student.course.ilike(s),
            )
        )

    if department:
        query = query.filter(Student.department == department.strip())

    if status in ["Active", "Inactive"]:
        query = query.filter(Student.status == status)

    sort_column_map = {
        "full_name": Student.full_name,
        "admission_number": Student.admission_number,
        "department": Student.department,
        "course": Student.course,
        "year": Student.year,
        "status": Student.status,
        "created_at": Student.created_at,
    }
    sort_col = sort_column_map.get(sort_by, Student.full_name)
    if order.lower() == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(asc(sort_col))

    return paginate_query(query, page=page, per_page=per_page)

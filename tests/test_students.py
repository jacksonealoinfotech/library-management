import pytest
from app.models.student import Student

def test_add_student_success(auth_client, db):
    """Test adding a new student member."""
    data = {
        "admission_number": "ST-999-001",
        "full_name": "Maya Lin",
        "email": "maya.lin@test.edu",
        "phone": "+1 555-8899",
        "department": "Computer Science",
        "course": "B.Tech Computer Science",
        "year": "2nd Year",
        "address": "Campus Dormitory",
        "date_of_birth": "2004-06-15",
        "status_val": "Active"
    }
    response = auth_client.post("/students/add", data=data, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/students"

    student = db.query(Student).filter(Student.admission_number == "ST-999-001").first()
    assert student is not None
    assert student.full_name == "Maya Lin"
    assert student.status == "Active"

def test_add_student_duplicate_admission_number(auth_client, db):
    """Test registering student with duplicate admission number fails."""
    s1 = Student(
        admission_number="ADM-DUP-01",
        full_name="Original Student",
        email="orig@test.edu",
        phone="555-1111",
        department="IT",
        course="B.Sc",
        year="1st Year",
        status="Active"
    )
    db.add(s1)
    db.commit()

    data = {
        "admission_number": "ADM-DUP-01",
        "full_name": "New Student",
        "email": "new@test.edu",
        "phone": "555-2222",
        "department": "IT",
        "course": "B.Sc",
        "year": "1st Year",
        "status_val": "Active"
    }
    response = auth_client.post("/students/add", data=data, follow_redirects=False)
    assert response.status_code == 400
    assert "already exists" in response.text

def test_edit_student(auth_client, db):
    """Test updating student details."""
    student = Student(
        admission_number="ADM-EDIT-01",
        full_name="Pre Edit Name",
        email="pre@test.edu",
        phone="555-3333",
        department="Mechanical",
        course="B.Tech",
        year="1st Year",
        status="Active"
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    edit_data = {
        "admission_number": "ADM-EDIT-01",
        "full_name": "Post Edit Name",
        "email": "post@test.edu",
        "phone": "555-4444",
        "department": "Mechanical Engineering",
        "course": "B.Tech Mechanical",
        "year": "2nd Year",
        "address": "New Address",
        "status_val": "Inactive"
    }
    response = auth_client.post(f"/students/{student.id}/edit", data=edit_data, follow_redirects=False)
    assert response.status_code == 303

    db.refresh(student)
    assert student.full_name == "Post Edit Name"
    assert student.email == "post@test.edu"
    assert student.status == "Inactive"

def test_delete_student(auth_client, db):
    """Test deleting student record."""
    student = Student(
        admission_number="ADM-DEL-01",
        full_name="To Delete",
        email="del@test.edu",
        phone="555-5555",
        department="Civil",
        course="B.Tech",
        year="1st Year",
        status="Active"
    )
    db.add(student)
    db.commit()
    sid = student.id

    response = auth_client.post(f"/students/{sid}/delete", follow_redirects=False)
    assert response.status_code == 303
    assert db.query(Student).filter(Student.id == sid).first() is None

def test_search_students(auth_client, db):
    """Test student search filtering."""
    s1 = Student(admission_number="ADM-SEARCH-1", full_name="Samantha Ray", email="sam@test.edu", phone="555-1001", department="Physics", course="B.Sc", year="1st Year", status="Active")
    s2 = Student(admission_number="ADM-SEARCH-2", full_name="Oliver Queen", email="oliver@test.edu", phone="555-1002", department="Arts", course="B.A", year="1st Year", status="Active")
    db.add_all([s1, s2])
    db.commit()

    response = auth_client.get("/students?search=Samantha")
    assert response.status_code == 200
    assert "Samantha Ray" in response.text
    assert "Oliver Queen" not in response.text

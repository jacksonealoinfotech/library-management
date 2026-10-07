import pytest
from datetime import date, timedelta
from app.models.book import Book
from app.models.student import Student
from app.models.transaction import Transaction

def test_successful_issue_and_inventory_decrement(auth_client, db):
    """Test issuing a book decrements available copies and creates an Issued transaction."""
    book = Book(isbn="978-CIRC-01", title="Circulation Test Book", author="Author", category="General", total_copies=3, available_copies=3)
    student = Student(admission_number="ADM-CIRC-01", full_name="Circulation Student", email="circ@test.edu", phone="555-0001", department="CS", course="B.Tech", year="1st Year", status="Active")
    db.add_all([book, student])
    db.commit()

    issue_data = {
        "student_id": student.id,
        "book_id": book.id,
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=14)).isoformat()
    }
    response = auth_client.post("/issue", data=issue_data, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/issued-books"

    # Verify inventory was decremented
    db.refresh(book)
    assert book.available_copies == 2

    # Verify transaction record
    tx = db.query(Transaction).filter(Transaction.book_id == book.id, Transaction.student_id == student.id).first()
    assert tx is not None
    assert tx.status == "Issued"
    assert tx.return_date is None

def test_issue_rejected_when_no_copies_available(auth_client, db):
    """Test issuing fails when available_copies is 0."""
    book = Book(isbn="978-CIRC-NO-COPY", title="Sold Out Book", author="Author", category="General", total_copies=1, available_copies=0)
    student = Student(admission_number="ADM-CIRC-02", full_name="Student Two", email="s2@test.edu", phone="555-0002", department="CS", course="B.Tech", year="1st Year", status="Active")
    db.add_all([book, student])
    db.commit()

    issue_data = {
        "student_id": student.id,
        "book_id": book.id,
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=14)).isoformat()
    }
    response = auth_client.post("/issue", data=issue_data, follow_redirects=False)
    assert response.status_code == 400
    assert "No copies are currently available" in response.text

def test_issue_rejected_for_inactive_student(auth_client, db):
    """Test inactive student cannot issue books."""
    book = Book(isbn="978-CIRC-INACTIVE", title="Book for Inactive", author="Author", category="General", total_copies=2, available_copies=2)
    student = Student(admission_number="ADM-CIRC-03", full_name="Inactive Student", email="s3@test.edu", phone="555-0003", department="CS", course="B.Tech", year="1st Year", status="Inactive")
    db.add_all([book, student])
    db.commit()

    issue_data = {
        "student_id": student.id,
        "book_id": book.id,
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=14)).isoformat()
    }
    response = auth_client.post("/issue", data=issue_data, follow_redirects=False)
    assert response.status_code == 400
    assert "Inactive" in response.text

def test_issue_rejected_when_max_limit_reached(auth_client, db):
    """Test student cannot exceed 3 active issued books."""
    b1 = Book(isbn="978-LIMIT-01", title="Limit Book 1", author="Author", category="Gen", total_copies=2, available_copies=2)
    b2 = Book(isbn="978-LIMIT-02", title="Limit Book 2", author="Author", category="Gen", total_copies=2, available_copies=2)
    b3 = Book(isbn="978-LIMIT-03", title="Limit Book 3", author="Author", category="Gen", total_copies=2, available_copies=2)
    b4 = Book(isbn="978-LIMIT-04", title="Limit Book 4", author="Author", category="Gen", total_copies=2, available_copies=2)
    student = Student(admission_number="ADM-LIMIT-01", full_name="Limit Student", email="limit@test.edu", phone="555-0004", department="CS", course="B.Tech", year="1st Year", status="Active")
    db.add_all([b1, b2, b3, b4, student])
    db.commit()

    # Issue 3 books directly
    for b in [b1, b2, b3]:
        tx = Transaction(book_id=b.id, student_id=student.id, issue_date=date.today(), due_date=date.today() + timedelta(days=14), status="Issued")
        b.available_copies -= 1
        db.add(tx)
    db.commit()

    # Attempt to issue 4th book
    issue_data = {
        "student_id": student.id,
        "book_id": b4.id,
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=14)).isoformat()
    }
    response = auth_client.post("/issue", data=issue_data, follow_redirects=False)
    assert response.status_code == 400
    assert "maximum book limit" in response.text

def test_issue_rejected_for_duplicate_same_book(auth_client, db):
    """Test student cannot issue a duplicate copy of the same book they already have out."""
    book = Book(isbn="978-DUP-ISSUE", title="Duplicate Loan Book", author="Author", category="Gen", total_copies=5, available_copies=5)
    student = Student(admission_number="ADM-DUP-ISSUE", full_name="Dup Student", email="dup@test.edu", phone="555-0005", department="CS", course="B.Tech", year="1st Year", status="Active")
    db.add_all([book, student])
    db.commit()

    # Issue first copy
    tx = Transaction(book_id=book.id, student_id=student.id, issue_date=date.today(), due_date=date.today() + timedelta(days=14), status="Issued")
    book.available_copies -= 1
    db.add(tx)
    db.commit()

    # Attempt to issue the exact same book to the same student again
    issue_data = {
        "student_id": student.id,
        "book_id": book.id,
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=14)).isoformat()
    }
    response = auth_client.post("/issue", data=issue_data, follow_redirects=False)
    assert response.status_code == 400
    assert "already has an active copy" in response.text

def test_successful_return_and_fine_calculation(auth_client, db):
    """Test returning an overdue book calculates fine correctly and restores copies."""
    book = Book(isbn="978-RETURN-FINE", title="Overdue Return Book", author="Author", category="Gen", total_copies=3, available_copies=2)
    student = Student(admission_number="ADM-RETURN-FINE", full_name="Late Student", email="late@test.edu", phone="555-0006", department="CS", course="B.Tech", year="1st Year", status="Active")
    db.add_all([book, student])
    db.commit()

    # Create transaction that was due 5 days ago
    past_due_date = date.today() - timedelta(days=5)
    issue_date = date.today() - timedelta(days=19)
    tx = Transaction(
        book_id=book.id,
        student_id=student.id,
        issue_date=issue_date,
        due_date=past_due_date,
        status="Issued",
        overdue_days=0,
        fine_amount=0.0
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    # Process return today (5 days overdue * $5/day = $25.00)
    response = auth_client.post(f"/return/{tx.id}", data={"return_date": date.today().isoformat()}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/issued-books"

    db.refresh(tx)
    assert tx.status == "Returned"
    assert tx.return_date == date.today()
    assert tx.overdue_days == 5
    assert tx.fine_amount == 25.0  # 5 days * $5

    # Check inventory restored
    db.refresh(book)
    assert book.available_copies == 3

def test_return_rejected_if_already_returned(auth_client, db):
    """Test returning a transaction that is already returned fails."""
    book = Book(isbn="978-ALREADY-RET", title="Already Returned Book", author="Author", category="Gen", total_copies=2, available_copies=2)
    student = Student(admission_number="ADM-ALREADY-RET", full_name="Student", email="ret@test.edu", phone="555-0007", department="CS", course="B.Tech", year="1st Year", status="Active")
    db.add_all([book, student])
    db.commit()

    tx = Transaction(
        book_id=book.id,
        student_id=student.id,
        issue_date=date.today() - timedelta(days=10),
        due_date=date.today() + timedelta(days=4),
        return_date=date.today() - timedelta(days=2),
        status="Returned",
        overdue_days=0,
        fine_amount=0.0
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    # Attempt to return again
    response = auth_client.post(f"/return/{tx.id}", follow_redirects=True)
    assert "already been returned" in response.text

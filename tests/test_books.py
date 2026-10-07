import pytest
from app.models.book import Book

def test_add_book_success(auth_client, db):
    """Test creating a new book."""
    data = {
        "isbn": "978-0111222333",
        "title": "Test Driven Development",
        "author": "Kent Beck",
        "category": "Software Engineering",
        "publisher": "Addison-Wesley",
        "publication_year": 2002,
        "total_copies": 5,
        "available_copies": 5,
        "shelf_number": "TDD-01",
        "description": "By example walkthrough of TDD."
    }
    response = auth_client.post("/books/add", data=data, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/books"

    # Verify book in database
    book = db.query(Book).filter(Book.isbn == "978-0111222333").first()
    assert book is not None
    assert book.title == "Test Driven Development"
    assert book.total_copies == 5
    assert book.available_copies == 5

def test_add_book_duplicate_isbn(auth_client, db):
    """Test creating a book with duplicate ISBN fails."""
    # First creation
    book = Book(
        isbn="978-DUPLICATE-01",
        title="First Instance",
        author="Author A",
        category="General",
        total_copies=2,
        available_copies=2
    )
    db.add(book)
    db.commit()

    # Attempt second creation with same ISBN
    data = {
        "isbn": "978-DUPLICATE-01",
        "title": "Second Instance",
        "author": "Author B",
        "category": "General",
        "total_copies": 3,
        "available_copies": 3
    }
    response = auth_client.post("/books/add", data=data, follow_redirects=False)
    assert response.status_code == 400
    assert "already exists" in response.text

def test_edit_book(auth_client, db):
    """Test editing an existing book."""
    book = Book(
        isbn="978-EDIT-ME-01",
        title="Original Title",
        author="Original Author",
        category="Category A",
        total_copies=4,
        available_copies=4
    )
    db.add(book)
    db.commit()
    db.refresh(book)

    edit_data = {
        "isbn": "978-EDIT-ME-01",
        "title": "Updated Title",
        "author": "Updated Author",
        "category": "Category B",
        "publisher": "New Publisher",
        "publication_year": 2024,
        "total_copies": 6,
        "available_copies": 6,
        "shelf_number": "NEW-SHELF",
        "description": "Updated desc"
    }
    response = auth_client.post(f"/books/{book.id}/edit", data=edit_data, follow_redirects=False)
    assert response.status_code == 303

    db.refresh(book)
    assert book.title == "Updated Title"
    assert book.author == "Updated Author"
    assert book.category == "Category B"
    assert book.total_copies == 6

def test_delete_book(auth_client, db):
    """Test deleting a book record."""
    book = Book(
        isbn="978-DELETE-ME",
        title="To Be Deleted",
        author="Some Author",
        category="Temporary",
        total_copies=1,
        available_copies=1
    )
    db.add(book)
    db.commit()
    book_id = book.id

    response = auth_client.post(f"/books/{book_id}/delete", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/books"

    deleted = db.query(Book).filter(Book.id == book_id).first()
    assert deleted is None

def test_search_books(auth_client, db):
    """Test backend book search filtering."""
    b1 = Book(isbn="978-SEARCH-01", title="Quantum Mechanics Fundamentals", author="David Griffiths", category="Physics", total_copies=2, available_copies=2)
    b2 = Book(isbn="978-SEARCH-02", title="Organic Chemistry Practice", author="Paula Bruice", category="Chemistry", total_copies=2, available_copies=2)
    db.add_all([b1, b2])
    db.commit()

    # Search for Quantum
    response = auth_client.get("/books?search=Quantum")
    assert response.status_code == 200
    assert "Quantum Mechanics" in response.text
    assert "Organic Chemistry" not in response.text

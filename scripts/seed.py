#!/usr/bin/env python3
"""
Seed Script for Library Management System
Populates the database with:
- Default Administrator (admin / admin123)
- 10 Realistic College Books
- 10 Registered Students
- Realistic circulation transactions (issued, overdue, returned with fines)
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add parent directory to sys.path so we can import from app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.book import Book
from app.models.student import Student
from app.models.transaction import Transaction
from app.services.setting_service import init_system_settings
from app.utils.auth import hash_password

def seed_database():
    print("Initializing database tables...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Initialize settings
        init_system_settings(db)
        print("✓ System settings initialized.")

        # 2. Default Administrator
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@library.edu",
                password_hash=hash_password("admin123")
            )
            db.add(admin)
            db.commit()
            print("✓ Created default administrator: admin / admin123")
        else:
            print("• Admin user already exists.")

        # 3. Seed 10 Books
        books_data = [
            {
                "isbn": "978-0132350884",
                "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
                "author": "Robert C. Martin",
                "category": "Computer Science",
                "publisher": "Prentice Hall",
                "publication_year": 2008,
                "total_copies": 5,
                "shelf_number": "CS-101",
                "description": "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees."
            },
            {
                "isbn": "978-0262033848",
                "title": "Introduction to Algorithms (4th Edition)",
                "author": "Thomas H. Cormen, Charles E. Leiserson",
                "category": "Computer Science",
                "publisher": "MIT Press",
                "publication_year": 2022,
                "total_copies": 4,
                "shelf_number": "CS-104",
                "description": "Comprehensive textbook on modern computer algorithms, data structures, and computational complexity."
            },
            {
                "isbn": "978-1449355730",
                "title": "Learning Python: Powerful Object-Oriented Programming",
                "author": "Mark Lutz",
                "category": "Programming",
                "publisher": "O'Reilly Media",
                "publication_year": 2013,
                "total_copies": 6,
                "shelf_number": "CS-108",
                "description": "In-depth, hands-on tutorial to both the Python core language and real-world application building."
            },
            {
                "isbn": "978-0134685991",
                "title": "Effective Java (3rd Edition)",
                "author": "Joshua Bloch",
                "category": "Programming",
                "publisher": "Addison-Wesley",
                "publication_year": 2018,
                "total_copies": 3,
                "shelf_number": "CS-112",
                "description": "Essential guidance and best practices for Java platform design patterns and idiom design."
            },
            {
                "isbn": "978-0321573513",
                "title": "Algorithms in C++ (Parts 1-4)",
                "author": "Robert Sedgewick",
                "category": "Computer Science",
                "publisher": "Addison-Wesley Professional",
                "publication_year": 2002,
                "total_copies": 4,
                "shelf_number": "CS-115",
                "description": "Focuses on fundamental algorithms and data structures with C++ implementations."
            },
            {
                "isbn": "978-0131103627",
                "title": "The C Programming Language (2nd Edition)",
                "author": "Brian W. Kernighan, Dennis M. Ritchie",
                "category": "Programming",
                "publisher": "Prentice Hall",
                "publication_year": 1988,
                "total_copies": 4,
                "shelf_number": "CS-120",
                "description": "The definitive guide to ANSI standard C programming by the language's creators."
            },
            {
                "isbn": "978-1119546016",
                "title": "Operating System Concepts (10th Edition)",
                "author": "Abraham Silberschatz, Peter B. Galvin",
                "category": "Computer Science",
                "publisher": "Wiley",
                "publication_year": 2018,
                "total_copies": 5,
                "shelf_number": "CS-205",
                "description": "Fundamental textbook covering process management, memory virtualisation, concurrency, and security."
            },
            {
                "isbn": "978-0073523323",
                "title": "Database System Concepts (7th Edition)",
                "author": "Abraham Silberschatz, Henry F. Korth",
                "category": "Database Systems",
                "publisher": "McGraw-Hill Education",
                "publication_year": 2019,
                "total_copies": 5,
                "shelf_number": "DB-101",
                "description": "Covers relational databases, SQL queries, transactions, concurrency control, and distributed storage."
            },
            {
                "isbn": "978-0133594140",
                "title": "Computer Networks (5th Edition)",
                "author": "Andrew S. Tanenbaum, David J. Wetherall",
                "category": "Networking",
                "publisher": "Pearson",
                "publication_year": 2010,
                "total_copies": 3,
                "shelf_number": "NET-201",
                "description": "Authoritative introduction to network architecture, OSI and TCP/IP models, and wireless protocols."
            },
            {
                "isbn": "978-0262035612",
                "title": "Deep Learning",
                "author": "Ian Goodfellow, Yoshua Bengio, Aaron Courville",
                "category": "Artificial Intelligence",
                "publisher": "MIT Press",
                "publication_year": 2016,
                "total_copies": 4,
                "shelf_number": "AI-301",
                "description": "The definitive textbook introducing machine learning mathematics, deep architectures, and applications."
            }
        ]

        created_books = []
        for b_data in books_data:
            existing = db.query(Book).filter(Book.isbn == b_data["isbn"]).first()
            if not existing:
                b = Book(
                    isbn=b_data["isbn"],
                    title=b_data["title"],
                    author=b_data["author"],
                    category=b_data["category"],
                    publisher=b_data["publisher"],
                    publication_year=b_data["publication_year"],
                    total_copies=b_data["total_copies"],
                    available_copies=b_data["total_copies"],
                    shelf_number=b_data["shelf_number"],
                    description=b_data["description"]
                )
                db.add(b)
                created_books.append(b)
            else:
                created_books.append(existing)

        db.commit()
        for b in created_books:
            db.refresh(b)
        print(f"✓ Seeded {len(created_books)} catalog books.")

        # 4. Seed 10 Students
        students_data = [
            {
                "admission_number": "CS-2023-0101",
                "full_name": "Aarav Sharma",
                "email": "aarav.sharma@apex.edu",
                "phone": "+1 555-0101",
                "department": "Computer Science",
                "course": "B.Tech Computer Science",
                "year": "3rd Year",
                "address": "Campus Hostel Block A, Room 302",
                "date_of_birth": date(2003, 5, 14),
                "status": "Active"
            },
            {
                "admission_number": "CS-2023-0102",
                "full_name": "Sophia Chen",
                "email": "sophia.chen@apex.edu",
                "phone": "+1 555-0102",
                "department": "Computer Science",
                "course": "B.Tech Computer Science",
                "year": "3rd Year",
                "address": "Campus Hostel Block B, Room 114",
                "date_of_birth": date(2003, 9, 21),
                "status": "Active"
            },
            {
                "admission_number": "IT-2024-0201",
                "full_name": "Marcus Johnson",
                "email": "marcus.j@apex.edu",
                "phone": "+1 555-0103",
                "department": "Information Technology",
                "course": "B.Sc Information Technology",
                "year": "2nd Year",
                "address": "452 University Ave, City",
                "date_of_birth": date(2004, 3, 11),
                "status": "Active"
            },
            {
                "admission_number": "IT-2024-0202",
                "full_name": "Priya Patel",
                "email": "priya.patel@apex.edu",
                "phone": "+1 555-0104",
                "department": "Information Technology",
                "course": "B.Sc Information Technology",
                "year": "2nd Year",
                "address": "Campus Hostel Block B, Room 204",
                "date_of_birth": date(2004, 11, 28),
                "status": "Active"
            },
            {
                "admission_number": "AI-2023-0301",
                "full_name": "Liam O'Connor",
                "email": "liam.oc@apex.edu",
                "phone": "+1 555-0105",
                "department": "Artificial Intelligence",
                "course": "M.Tech Data Science & AI",
                "year": "Post Graduate",
                "address": "Graduate Housing Wing C, Room 42",
                "date_of_birth": date(2000, 7, 19),
                "status": "Active"
            },
            {
                "admission_number": "EC-2022-0401",
                "full_name": "Elena Rostova",
                "email": "elena.r@apex.edu",
                "phone": "+1 555-0106",
                "department": "Electronics & Comm.",
                "course": "B.Tech Electronics",
                "year": "4th Year",
                "address": "812 College Blvd, Apt 4B",
                "date_of_birth": date(2002, 1, 9),
                "status": "Active"
            },
            {
                "admission_number": "ME-2025-0501",
                "full_name": "David Kim",
                "email": "david.kim@apex.edu",
                "phone": "+1 555-0107",
                "department": "Mechanical Engineering",
                "course": "B.Tech Mechanical",
                "year": "1st Year",
                "address": "Campus Hostel Block C, Room 102",
                "date_of_birth": date(2005, 8, 30),
                "status": "Active"
            },
            {
                "admission_number": "CS-2022-0103",
                "full_name": "Fatima Al-Mansoor",
                "email": "fatima.m@apex.edu",
                "phone": "+1 555-0108",
                "department": "Computer Science",
                "course": "B.Tech Computer Science",
                "year": "4th Year",
                "address": "Campus Hostel Block B, Room 410",
                "date_of_birth": date(2002, 12, 5),
                "status": "Active"
            },
            {
                "admission_number": "BA-2024-0601",
                "full_name": "Ethan Wright",
                "email": "ethan.w@apex.edu",
                "phone": "+1 555-0109",
                "department": "Business Administration",
                "course": "MBA Technology Management",
                "year": "Post Graduate",
                "address": "129 Elm St, City",
                "date_of_birth": date(2001, 4, 17),
                "status": "Active"
            },
            {
                "admission_number": "CS-2021-0099",
                "full_name": "Lucas Morales (Inactive)",
                "email": "lucas.m@apex.edu",
                "phone": "+1 555-0110",
                "department": "Computer Science",
                "course": "B.Tech Computer Science",
                "year": "4th Year",
                "address": "Off-campus Residence",
                "date_of_birth": date(2001, 10, 3),
                "status": "Inactive"
            }
        ]

        created_students = []
        for s_data in students_data:
            existing = db.query(Student).filter(Student.admission_number == s_data["admission_number"]).first()
            if not existing:
                s = Student(
                    admission_number=s_data["admission_number"],
                    full_name=s_data["full_name"],
                    email=s_data["email"],
                    phone=s_data["phone"],
                    department=s_data["department"],
                    course=s_data["course"],
                    year=s_data["year"],
                    address=s_data["address"],
                    date_of_birth=s_data["date_of_birth"],
                    status=s_data["status"]
                )
                db.add(s)
                created_students.append(s)
            else:
                created_students.append(existing)

        db.commit()
        for s in created_students:
            db.refresh(s)
        print(f"✓ Seeded {len(created_students)} student records.")

        # 5. Seed Sample Transactions
        # Only seed if no transactions exist yet
        tx_count = db.query(Transaction).count()
        if tx_count == 0:
            today = date.today()
            sample_txs = [
                # 1. Past Returned on time (no fine)
                {
                    "book_idx": 0, "student_idx": 0,
                    "issue_date": today - timedelta(days=25),
                    "due_date": today - timedelta(days=11),
                    "return_date": today - timedelta(days=12),
                    "status": "Returned", "overdue_days": 0, "fine_amount": 0.0
                },
                # 2. Past Returned overdue (fine charged)
                {
                    "book_idx": 1, "student_idx": 1,
                    "issue_date": today - timedelta(days=30),
                    "due_date": today - timedelta(days=16),
                    "return_date": today - timedelta(days=12),
                    "status": "Returned", "overdue_days": 4, "fine_amount": 20.0
                },
                # 3. Past Returned on time
                {
                    "book_idx": 2, "student_idx": 2,
                    "issue_date": today - timedelta(days=20),
                    "due_date": today - timedelta(days=6),
                    "return_date": today - timedelta(days=8),
                    "status": "Returned", "overdue_days": 0, "fine_amount": 0.0
                },
                # 4. Past Returned overdue (fine charged)
                {
                    "book_idx": 7, "student_idx": 4,
                    "issue_date": today - timedelta(days=28),
                    "due_date": today - timedelta(days=14),
                    "return_date": today - timedelta(days=10),
                    "status": "Returned", "overdue_days": 4, "fine_amount": 20.0
                },
                # 5. Currently Issued: On Schedule
                {
                    "book_idx": 0, "student_idx": 1,
                    "issue_date": today - timedelta(days=4),
                    "due_date": today + timedelta(days=10),
                    "return_date": None,
                    "status": "Issued", "overdue_days": 0, "fine_amount": 0.0
                },
                # 6. Currently Issued: On Schedule
                {
                    "book_idx": 9, "student_idx": 4,
                    "issue_date": today - timedelta(days=2),
                    "due_date": today + timedelta(days=12),
                    "return_date": None,
                    "status": "Issued", "overdue_days": 0, "fine_amount": 0.0
                },
                # 7. Currently Issued: Overdue! (Due 5 days ago)
                {
                    "book_idx": 2, "student_idx": 3,
                    "issue_date": today - timedelta(days=19),
                    "due_date": today - timedelta(days=5),
                    "return_date": None,
                    "status": "Issued", "overdue_days": 0, "fine_amount": 0.0
                },
                # 8. Currently Issued: Overdue! (Due 2 days ago)
                {
                    "book_idx": 3, "student_idx": 5,
                    "issue_date": today - timedelta(days=16),
                    "due_date": today - timedelta(days=2),
                    "return_date": None,
                    "status": "Issued", "overdue_days": 0, "fine_amount": 0.0
                },
                # 9. Additional past returned loan
                {
                    "book_idx": 0, "student_idx": 6,
                    "issue_date": today - timedelta(days=15),
                    "due_date": today - timedelta(days=1),
                    "return_date": today - timedelta(days=2),
                    "status": "Returned", "overdue_days": 0, "fine_amount": 0.0
                }
            ]

            for tx_info in sample_txs:
                b = created_books[tx_info["book_idx"]]
                s = created_students[tx_info["student_idx"]]
                tx = Transaction(
                    book_id=b.id,
                    student_id=s.id,
                    issue_date=tx_info["issue_date"],
                    due_date=tx_info["due_date"],
                    return_date=tx_info["return_date"],
                    status=tx_info["status"],
                    overdue_days=tx_info["overdue_days"],
                    fine_amount=tx_info["fine_amount"]
                )
                db.add(tx)
                if tx_info["status"] == "Issued":
                    b.available_copies = max(0, b.available_copies - 1)

            db.commit()
            print("✓ Seeded sample circulation transactions (issued, overdue, and returned with fines).")
        else:
            print(f"• Transactions already exist ({tx_count} records).")

        print("\n=======================================================")
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("Default Administrator:")
        print("  Username: admin")
        print("  Password: admin123")
        print("=======================================================")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}", file=sys.stderr)
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

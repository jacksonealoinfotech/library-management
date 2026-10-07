# Library Management System Using Python FastAPI

A modern, production-grade web-based **Library Management System (LMS)** designed for colleges and universities to replace manual paper record-keeping. Built with **Python 3.11+**, **FastAPI**, **SQLAlchemy ORM**, **SQLite**, **Jinja2 Templates**, and **Bootstrap 5**.

---

## 1. Project Abstract

In many academic institutions, library circulation is still managed via physical ledgers or fragmented spreadsheet systems. This manual approach leads to untracked overdue books, lost inventory, inaccurate fine calculations, and significant administrative overhead.

The **Library Management System Using Python FastAPI** is an automated, web-based administrative dashboard that provides end-to-end management of college library operations:
* Secure administrator authentication with session control and cryptographic password hashing (bcrypt).
* Full CRUD inventory tracking for catalog books with physical shelf assignment.
* Complete registration and lifecycle status management for student members.
* Real-time book circulation (issuing, due date scheduling, returning).
* Automated overdue detection and configurable daily fine calculations.
* Backend-driven multi-criteria search and filter queries.
* Comprehensive circulation transaction audit trails.
* Analytical dashboard with visual distribution charts (Chart.js) and printable reports with CSV export.

---

## 2. Technology Stack

### Backend
* **Python**: 3.11+ (Tested on Python 3.14)
* **Web Framework**: FastAPI
* **ASGI Server**: Uvicorn
* **Database ORM**: SQLAlchemy 2.0
* **Data Validation**: Pydantic v2
* **Database Engine**: SQLite 3 (stored as `library.db`)
* **Templating Engine**: Jinja2

### Frontend
* **HTML5 & CSS3**: Semantic markup with responsive custom styling
* **CSS Framework**: Bootstrap 5.3 (Clean, responsive dashboard layout)
* **Icons**: Bootstrap Icons (v1.11)
* **Data Visualization**: Chart.js (v4.4)
* **Client Scripting**: Vanilla JavaScript (ES6+)

### Supporting Libraries
* `python-multipart`: Form data streaming and file uploads
* `python-dotenv`: Environment configuration management
* `bcrypt`: Password hashing with salt rounds
* `itsdangerous` & Starlette `SessionMiddleware`: Cryptographically signed cookie session management
* `pytest` & `httpx`: Automated testing suite

---

## 3. Key Features

### 🔐 1. Authentication & Security
* Session-based login with encrypted cookies and automatic expiry.
* Protected route enforcement: unauthenticated requests are redirected to `/login`.
* Passwords stored securely as bcrypt hashes; no plain-text passwords stored.
* Auto-initialized default admin account (`admin` / `admin123`).
* In-app administrator password change functionality.

### 📚 2. Catalog & Book Management
* Complete CRUD functionality: Add, view details, edit metadata, and delete books.
* Unique ISBN enforcement with format validation.
* Multi-copy inventory tracking: `total_copies` vs `available_copies`.
* Deletion protection: books currently checked out cannot be deleted until returned.
* Real-time search across Title, Author, ISBN, Category, and Shelf Location.
* Filtering by category and stock availability.
* Multi-column sorting and pagination.

### 🎓 3. Student Member Management
* Complete CRUD functionality: Register, view student profile, edit, and delete students.
* Unique College Admission / Roll Number enforcement.
* Contact information validation (email, telephone).
* Department and academic year classification.
* Active / Inactive status tracking: Inactive students are automatically blocked from borrowing books.
* Deletion protection: students holding active books cannot be deleted until all loans are cleared.

### 🔄 4. Book Circulation (Issue & Return)
* **Issue Workflow (`/issue`)**:
  * Dropdown selection of available books and active students.
  * Validation: Student must be `Active`.
  * Validation: Book must have `available_copies > 0`.
  * Validation: Student limit enforced (maximum 3 active loans by default).
  * Validation: No duplicate issues (student cannot borrow the same book twice simultaneously).
  * Decrements inventory upon successful checkout.
* **Return Workflow (`/return` and `/issued-books`)**:
  * Shows all currently checked-out books.
  * Automated overdue calculation: compares return date against due date.
  * Automated fine assessment: `Fine = Overdue Days × Fine Per Day`.
  * Restores available copies upon check-in.
  * Guard clause: already returned loans cannot be returned again.

### 📊 5. Dashboard & Analytics
* Five real-time KPI metric cards:
  1. Total Books (total physical copies)
  2. Available Books
  3. Issued Books
  4. Total Registered Students
  5. Overdue Books
* **Chart.js Visualizations**:
  * **Inventory Distribution**: Doughnut chart showing Available vs Issued copies.
  * **Circulation Activity**: Daily issue and return trend over the past 14 days.
  * **Popular Books**: Horizontal bar chart of the top 5 most borrowed titles.
* Recent transactions feed with quick-action return modals.

### 📑 6. Reports & Export
* Comprehensive circulation reporting filtered by custom date ranges.
* Summary statistics: Total Titles, Registered Members, Period Circulation, and Total Fines.
* Top 10 most borrowed books and top 10 most active student borrowers.
* **CSV Export**: One-click download of filtered audit logs.
* **Print-Optimized View**: Built-in CSS `@media print` rules for clean hard-copy printing.

### ⚙️ 7. System Settings
* In-database configurable parameters with fallback to `.env`:
  * Library Display Name
  * Maximum Books per Student (default: 3)
  * Overdue Fine Rate per Day (default: $5.00)
  * Default Lending Duration (default: 14 days)
* Administrator password reset.

---

## 4. Database Architecture & Schema

The application uses SQLite (`library.db`) with SQLAlchemy ORM models and enforced foreign keys (`PRAGMA foreign_keys = ON`).

```
                    ┌─────────────────────────┐
                    │          users          │
                    ├─────────────────────────┤
                    │ id (PK)                 │
                    │ username (UNIQUE)       │
                    │ email (UNIQUE)          │
                    │ password_hash           │
                    │ created_at              │
                    └─────────────────────────┘

 ┌─────────────────────────┐           ┌─────────────────────────┐
 │          books          │           │        students         │
 ├─────────────────────────┤           ├─────────────────────────┤
 │ id (PK)                 │           │ id (PK)                 │
 │ isbn (UNIQUE)           │           │ admission_number (UNQ)  │
 │ title                   │           │ full_name               │
 │ author                  │           │ email                   │
 │ category                │           │ phone                   │
 │ publisher               │           │ department              │
 │ publication_year        │           │ course                  │
 │ total_copies            │           │ year                    │
 │ available_copies        │           │ address                 │
 │ shelf_number            │           │ date_of_birth           │
 │ description             │           │ registration_date       │
 │ created_at / updated_at │           │ status (Active/Inactive)│
 └───────────┬─────────────┘           └───────────┬─────────────┘
             │ 1                                   │ 1
             │                                     │
             │ *                                   │ *
       ┌─────┴─────────────────────────────────────┴─────┐
       │                  transactions                   │
       ├─────────────────────────────────────────────────┤
       │ id (PK)                                         │
       │ book_id (FK -> books.id)                        │
       │ student_id (FK -> students.id)                  │
       │ issue_date                                      │
       │ due_date                                        │
       │ return_date                                     │
       │ status (Issued / Returned / Overdue)            │
       │ overdue_days                                    │
       │ fine_amount                                     │
       │ created_at / updated_at                         │
       └─────────────────────────────────────────────────┘
```

### Business Rules & Constraints
1. **Available Copies**: `0 <= available_copies <= total_copies`.
2. **Quota Limit**: An active student cannot have more than `MAX_BOOKS_PER_STUDENT` concurrent `Issued` loans.
3. **No Duplicate Loans**: A student cannot have another `Issued` transaction for the same `book_id`.
4. **Member Status**: Only students with `status == "Active"` can borrow books.
5. **Overdue Calculation**:
   $$\text{Overdue Days} = \max(0, \text{Return Date} - \text{Due Date})$$
   $$\text{Fine Amount} = \text{Overdue Days} \times \text{FINE\_PER\_DAY}$$

---

## 5. Project Directory Structure

```text
library-management-system/
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & middleware
│   ├── config.py                # Environment and configuration settings
│   ├── database.py              # SQLAlchemy engine, session maker, base model
│   ├── templating.py            # Jinja2 environment and custom filters
│   │
│   ├── models/                  # SQLAlchemy ORM database models
│   │   ├── __init__.py
│   │   ├── user.py              # User model (administrators)
│   │   ├── book.py              # Book model
│   │   ├── student.py           # Student model
│   │   ├── transaction.py       # Circulation transaction model
│   │   └── setting.py           # Persistent system settings model
│   │
│   ├── schemas/                 # Pydantic v2 validation models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── book.py
│   │   ├── student.py
│   │   └── transaction.py
│   │
│   ├── routers/                 # Modular HTTP route handlers
│   │   ├── __init__.py
│   │   ├── auth.py              # Login / Logout routes
│   │   ├── dashboard.py         # Dashboard analytics route
│   │   ├── books.py             # Books CRUD & search
│   │   ├── students.py          # Students CRUD & search
│   │   ├── circulation.py       # Issue, Return, and Issued Books routes
│   │   ├── transactions.py      # History audit log routes
│   │   ├── reports.py           # Analytics reporting & CSV export
│   │   └── settings.py          # System configuration routes
│   │
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Authentication & password logic
│   │   ├── book_service.py      # Book business logic & filters
│   │   ├── student_service.py   # Student business logic & filters
│   │   ├── transaction_service.py # Issue, Return, and Fine logic
│   │   ├── report_service.py    # Metric aggregation & charts dataset
│   │   └── setting_service.py   # System settings management
│   │
│   ├── utils/                   # Reusable helpers & auth utilities
│   │   ├── __init__.py
│   │   ├── auth.py              # Password hashing & session dependencies
│   │   └── helpers.py           # Flash messages, overdue math, pagination
│   │
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── base.html            # Main dashboard shell & navigation
│   │   ├── login.html           # Admin login page
│   │   ├── dashboard.html       # Metrics & charts dashboard
│   │   ├── settings.html        # System settings & password change
│   │   ├── books/
│   │   │   ├── index.html       # Books list, search, filter, pagination
│   │   │   ├── add.html         # Book creation form
│   │   │   ├── edit.html        # Book edit form
│   │   │   └── detail.html      # Book detail & lending history
│   │   ├── students/
│   │   │   ├── index.html       # Students directory
│   │   │   ├── add.html         # Student registration form
│   │   │   ├── edit.html        # Student edit form
│   │   │   └── detail.html      # Student profile & loan history
│   │   ├── circulation/
│   │   │   ├── issue.html       # Book checkout form
│   │   │   ├── return.html      # Book return search & process
│   │   │   └── issued_books.html# Active loans & overdue tracker
│   │   ├── transactions/
│   │   │   ├── index.html       # Complete transaction audit log
│   │   │   └── detail.html      # Single transaction view
│   │   ├── reports/
│   │   │   └── index.html       # Analytics, top books, CSV export, print
│   │   └── errors/
│   │       ├── 403.html         # Forbidden access page
│   │       ├── 404.html         # Not found page
│   │       └── 500.html         # Internal server error page
│   │
│   └── static/                  # Static assets
│       ├── css/
│       │   └── style.css        # Professional dark-blue dashboard styling
│       ├── js/
│       │   └── app.js           # Modal handlers & responsive scripts
│       └── images/
│
├── scripts/
│   └── seed.py                  # Database seeder (10 books, 10 students, sample loans)
│
├── tests/                       # Automated pytest suite (28 tests)
│   ├── __init__.py
│   ├── conftest.py              # Test database and client fixtures
│   ├── test_auth.py             # Authentication tests
│   ├── test_books.py            # Books CRUD & search tests
│   ├── test_students.py         # Students CRUD & search tests
│   ├── test_circulation.py      # Issue, return, & fine calculation tests
│   ├── test_reports.py          # Dashboard & CSV export tests
│   └── test_settings.py         # System settings tests
│
├── .env                         # Local environment variables
├── .env.example                 # Template environment variables
├── .gitignore                   # Git ignore file
├── requirements.txt             # Project dependencies
├── README.md                    # Project documentation
└── library.db                   # SQLite database
```

---

## 6. Installation & Setup Guide

### Step 1: Clone or Navigate to the Project Directory

```bash
cd /Users/jackson/.gemini/antigravity/scratch/library-management-system
```

### Step 2: Create and Activate a Python Virtual Environment

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### Step 3: Install Required Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Copy the example environment configuration:

```bash
cp .env.example .env
```

Verify your `.env` contains:
```ini
DATABASE_URL=sqlite:///./library.db
SECRET_KEY=collegelibrary_secret_key_antigravity_dev_2026_x89
SESSION_EXPIRE_MINUTES=60
MAX_BOOKS_PER_STUDENT=3
FINE_PER_DAY=5.0
LIBRARY_NAME=Apex Institute Central Library
DEFAULT_DUE_DAYS=14
```

> [!IMPORTANT]
> **Production Notice**: Always update `SECRET_KEY` with a strong, random 32+ character key in production environments.

### Step 5: Seed Sample Database Records

Run the seed script to create all database tables, the default administrator account, 10 realistic college books, 10 student profiles, and sample circulation records:

```bash
python scripts/seed.py
```

Output:
```text
Initializing database tables...
✓ System settings initialized.
✓ Created default administrator: admin / admin123
✓ Seeded 10 catalog books.
✓ Seeded 10 student records.
✓ Seeded sample circulation transactions.
DATABASE SEEDING COMPLETED SUCCESSFULLY!
```

---

## 7. How to Run the Application

Start the FastAPI application using the Uvicorn ASGI server:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser and navigate to:
```
http://127.0.0.1:8000
```

### Default Login Credentials

* **URL**: `http://127.0.0.1:8000/login`
* **Username**: `admin`
* **Password**: `admin123`

> [!NOTE]
> For security, please navigate to **Settings** (`/settings`) after your first login to change the default administrator password.

---

## 8. Main Application Routes

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/` | Redirects to `/dashboard` | Public |
| `GET` | `/login` | Administrator login page | Public |
| `POST` | `/login` | Authenticates administrator credentials | Public |
| `GET` | `/logout` | Clears administrator session | Authenticated |
| `GET` | `/dashboard` | Analytical dashboard with KPI cards & Chart.js | Authenticated |
| `GET` | `/books` | All books catalog with search, filter, sort & pagination | Authenticated |
| `GET` | `/books/add` | Book creation form | Authenticated |
| `POST` | `/books/add` | Submits new book record | Authenticated |
| `GET` | `/books/{id}` | Book details & circulation history | Authenticated |
| `GET` | `/books/{id}/edit`| Book editing form | Authenticated |
| `POST` | `/books/{id}/edit`| Updates book record | Authenticated |
| `POST` | `/books/{id}/delete`| Deletes book record (if not currently issued) | Authenticated |
| `GET` | `/students` | Students directory with search & department filters | Authenticated |
| `GET` | `/students/add` | Student registration form | Authenticated |
| `POST` | `/students/add` | Submits new student registration | Authenticated |
| `GET` | `/students/{id}` | Student profile & borrowing status | Authenticated |
| `GET` | `/students/{id}/edit`| Student edit form | Authenticated |
| `POST` | `/students/{id}/edit`| Updates student record | Authenticated |
| `POST` | `/students/{id}/delete`| Deletes student (if holding no unreturned books) | Authenticated |
| `GET` | `/issue` | Book loan checkout form | Authenticated |
| `POST` | `/issue` | Issues book to student and decrements copy | Authenticated |
| `GET` | `/issued-books` | Currently issued loans & overdue monitoring | Authenticated |
| `GET` | `/return` | Return book lookup page | Authenticated |
| `POST` | `/return/{id}` | Returns book, calculates overdue fine, increments copy | Authenticated |
| `GET` | `/transactions` | Complete audit log of all lending transactions | Authenticated |
| `GET` | `/transactions/{id}`| Detailed individual transaction inspection | Authenticated |
| `GET` | `/reports` | Analytics report, top books, top borrowers | Authenticated |
| `GET` | `/reports/export` | Exports transaction audit log to CSV | Authenticated |
| `GET` | `/settings` | System parameters & admin password change | Authenticated |
| `POST` | `/settings` | Saves system configuration changes | Authenticated |
| `POST` | `/settings/password`| Changes administrator password | Authenticated |

---

## 9. Running Automated Tests

The project includes an automated test suite containing **28 tests** covering authentication, books CRUD, students CRUD, issue business logic, return business logic, fines, dashboard metrics, reports, and settings.

To execute the test suite:

```bash
pytest tests/ -v
```

Expected output:
```text
======================== 28 passed, 1 warning in 4.53s =========================
```

---

## 10. College Project Viva / Review Guide

When presenting this project during a viva or practical project demonstration, highlight the following design decisions:

1. **Clean Layered Architecture**:
   - `models`: SQLAlchemy database tables and relationships.
   - `schemas`: Pydantic input validation models preventing malformed inputs.
   - `services`: Business logic layer encapsulating transactions, loan eligibility, fine calculations, and inventory updates.
   - `routers`: Web presentation controller layer parsing HTTP requests and rendering Jinja2 views.
   - `templates` & `static`: Responsive Bootstrap 5 user interface.

2. **Concurrency & Data Integrity**:
   - Atomic copy counters (`available_copies` decrement/increment in the same database transaction as the loan record creation/closure).
   - Foreign keys with `PRAGMA foreign_keys = ON` on SQLite preventing orphaned transaction records.
   - Safe delete rules: books and students with active checkouts cannot be deleted.

3. **User Experience (UX)**:
   - Dismissible flash alerts giving feedback for every successful or failed action.
   - Confirmation modals before destructive operations (Delete book, Delete student, Return book).
   - Overdue badge highlights with real-time fine estimation prior to confirm check-in.

---

## 11. Potential Future Enhancements

* **Email Notifications**: Integration with Celery/FastAPI BackgroundTasks to send automated reminder emails 2 days before the due date.
* **Barcoding / QR Scanner**: Integration with webcam scanning for student ID badges and book barcodes.
* **Online Payment Gateway**: Integration with Stripe or PayPal for digital fine settlement.
* **Student Self-Service Portal**: Read-only login for students to view their own loan history and reserve books.

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.book import Book
from app.models.student import Student
from app.services.setting_service import init_system_settings
from app.utils.auth import hash_password

# Use an isolated test database
TEST_DB_PATH = Path("./test_library.db")
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_library.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test tables before session and clean up after session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    init_system_settings(db)
    # Ensure admin user
    if not db.query(User).filter(User.username == "admin").first():
        admin = User(
            username="admin",
            email="admin@test.edu",
            password_hash=hash_password("admin123")
        )
        db.add(admin)
        db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass

@pytest.fixture
def db():
    """Provide a fresh database session per test with clean isolation."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    """Unauthenticated TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_client(client):
    """TestClient authenticated as the default administrator."""
    # Perform login
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False
    )
    assert response.status_code == 303
    return client

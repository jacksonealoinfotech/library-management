import pytest

def test_login_page_renders(client):
    """Verify login page displays properly for guests."""
    response = client.get("/login")
    assert response.status_code == 200
    assert "Admin Login" in response.text or "Sign In" in response.text

def test_login_success(client):
    """Verify administrator can log in with valid credentials."""
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"

def test_login_failure_wrong_password(client):
    """Verify login fails with wrong password."""
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrongpassword"},
        follow_redirects=False
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.text

def test_login_failure_nonexistent_user(client):
    """Verify login fails with nonexistent username."""
    response = client.post(
        "/login",
        data={"username": "fakeuser", "password": "anypassword"},
        follow_redirects=False
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.text

def test_protected_routes_redirect_unauthenticated(client):
    """Verify unauthenticated access to dashboard/books redirects to login."""
    protected_urls = ["/dashboard", "/books", "/students", "/issue", "/issued-books", "/reports", "/settings"]
    for url in protected_urls:
        response = client.get(url, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

def test_logout(auth_client):
    """Verify logging out clears session and redirects to login."""
    response = auth_client.get("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    # Subsequent access should be blocked
    resp_after = auth_client.get("/dashboard", follow_redirects=False)
    assert resp_after.status_code == 303
    assert resp_after.headers["location"] == "/login"

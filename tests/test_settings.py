import pytest
from app.services.setting_service import get_all_settings

def test_settings_page_renders(auth_client):
    """Test settings page displays current configuration."""
    response = auth_client.get("/settings")
    assert response.status_code == 200
    assert "Circulation & Library Rules" in response.text or "Library Rules" in response.text
    assert "Change Administrator Password" in response.text

def test_update_settings(auth_client, db):
    """Test updating library configurations."""
    update_data = {
        "library_name": "Updated University Library",
        "max_books_per_student": 5,
        "fine_per_day": 10.0,
        "default_due_days": 21
    }
    response = auth_client.post("/settings", data=update_data, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/settings"

    settings_dict = get_all_settings(db)
    assert settings_dict["library_name"] == "Updated University Library"
    assert settings_dict["max_books_per_student"] == 5
    assert settings_dict["fine_per_day"] == 10.0
    assert settings_dict["default_due_days"] == 21

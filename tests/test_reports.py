import pytest

def test_dashboard_metrics(auth_client):
    """Test dashboard page renders key metrics."""
    response = auth_client.get("/dashboard")
    assert response.status_code == 200
    assert "Total Books" in response.text
    assert "Available Books" in response.text
    assert "Issued Books" in response.text
    assert "Total Students" in response.text
    assert "Overdue Books" in response.text

def test_reports_page(auth_client):
    """Test reports page renders report tables and summaries."""
    response = auth_client.get("/reports")
    assert response.status_code == 200
    assert "Official Circulation" in response.text or "Library Reports" in response.text
    assert "Most Borrowed Titles" in response.text
    assert "Most Active Borrowers" in response.text

def test_reports_csv_export(auth_client):
    """Test CSV export endpoint generates CSV file."""
    response = auth_client.get("/reports/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "attachment; filename=" in response.headers.get("content-disposition", "")
    assert "Transaction ID,Book Title,ISBN,Student Name" in response.text

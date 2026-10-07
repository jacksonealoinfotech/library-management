from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.report_service import get_dashboard_statistics
from app.templating import templates
from app.utils.auth import require_auth

router = APIRouter(tags=["Dashboard"])

@router.get("/")
async def root_redirect():
    """Redirect root path to dashboard."""
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Render main administration dashboard with KPI metrics, charts, and recent activity."""
    stats = get_dashboard_statistics(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats,
            "active_page": "dashboard"
        }
    )

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.setting_service import get_all_settings, update_system_settings
from app.services.auth_service import update_admin_password
from app.templating import templates
from app.utils.auth import require_auth
from app.utils.helpers import flash

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """View and update system parameters and admin security settings."""
    current_settings = get_all_settings(db)
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "current_user": current_user,
            "settings": current_settings,
            "active_page": "settings"
        }
    )

@router.post("", response_class=HTMLResponse)
async def update_settings_submit(
    request: Request,
    library_name: str = Form(...),
    max_books_per_student: int = Form(...),
    fine_per_day: float = Form(...),
    default_due_days: int = Form(14),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Save updated system settings."""
    try:
        update_system_settings(
            db=db,
            library_name=library_name,
            max_books_per_student=max_books_per_student,
            fine_per_day=fine_per_day,
            default_due_days=default_due_days
        )
        flash(request, "Library settings updated successfully.", "success")
    except Exception as e:
        flash(request, f"Error updating settings: {e}", "danger")
    return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/password", response_class=HTMLResponse)
async def change_password_submit(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Handle administrator password update."""
    if new_password != confirm_password:
        flash(request, "New password and confirmation do not match.", "danger")
        return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)

    if len(new_password) < 6:
        flash(request, "New password must be at least 6 characters long.", "danger")
        return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)

    success = update_admin_password(
        db=db,
        user_id=current_user.id,
        current_password=current_password,
        new_password=new_password
    )
    if not success:
        flash(request, "Incorrect current password.", "danger")
    else:
        flash(request, "Administrator password changed successfully.", "success")

    return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)

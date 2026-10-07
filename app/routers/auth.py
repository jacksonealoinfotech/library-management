from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import authenticate_user
from app.templating import templates
from app.utils.helpers import flash

router = APIRouter(tags=["Authentication"])

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display the admin login page. If already authenticated, redirect to dashboard."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Authenticate administrator credentials and establish session."""
    user = authenticate_user(db, username=username, password=password)
    if not user:
        flash(request, "Invalid username or password. Please try again.", "danger")
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "username": username,
                "error": "Invalid username or password."
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Set user session
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    flash(request, f"Welcome back, {user.username}!", "success")
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
async def logout(request: Request):
    """Log out administrator and clear session data."""
    request.session.clear()
    flash(request, "You have been successfully logged out.", "info")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

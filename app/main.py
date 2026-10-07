import logging
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse

from app.config import settings
from app.database import init_db, SessionLocal
from app.services.auth_service import ensure_admin_user
from app.services.setting_service import init_system_settings
from app.templating import templates
from app.utils.auth import UnauthenticatedException
from app.utils.helpers import flash

from app.routers import (
    auth_router,
    dashboard_router,
    books_router,
    students_router,
    circulation_router,
    transactions_router,
    reports_router,
    settings_router,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("library_system")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown event management."""
    logger.info("Initializing database and verifying core configuration...")
    init_db()
    db = SessionLocal()
    try:
        ensure_admin_user(db)
        init_system_settings(db)
        logger.info("Database initialized successfully with default admin user and settings.")
    finally:
        db.close()
    yield
    logger.info("Shutting down Library Management System...")

# Initialize FastAPI application
app = FastAPI(
    title="Library Management System Using Python FastAPI",
    description="A complete web-based library management platform for universities and colleges.",
    version="1.0.0",
    lifespan=lifespan
)

# Session middleware with signed cookies
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=settings.SESSION_EXPIRE_MINUTES * 60,
    same_site="lax"
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Custom Exception Handlers
@app.exception_handler(UnauthenticatedException)
async def unauthenticated_handler(request: Request, exc: UnauthenticatedException):
    """Redirect unauthenticated users to the login page with an alert."""
    flash(request, exc.message, "warning")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Custom friendly error pages for standard HTTP status codes."""
    if exc.status_code == 404:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "detail": exc.detail},
            status_code=404
        )
    if exc.status_code == 403:
        return templates.TemplateResponse(
            "errors/403.html",
            {"request": request, "detail": exc.detail},
            status_code=403
        )
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request, "detail": exc.detail, "status_code": exc.status_code},
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Fallback handler to prevent raw unformatted tracebacks in production."""
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request, "detail": str(exc), "status_code": 500},
        status_code=500
    )

# Include Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(books_router)
app.include_router(students_router)
app.include_router(circulation_router)
app.include_router(transactions_router)
app.include_router(reports_router)
app.include_router(settings_router)

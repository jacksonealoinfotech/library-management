from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.books import router as books_router
from app.routers.students import router as students_router
from app.routers.circulation import router as circulation_router
from app.routers.transactions import router as transactions_router
from app.routers.reports import router as reports_router
from app.routers.settings import router as settings_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "books_router",
    "students_router",
    "circulation_router",
    "transactions_router",
    "reports_router",
    "settings_router",
]

from datetime import date, datetime
from typing import Any, Mapping
from fastapi import Request
from starlette.templating import Jinja2Templates, _TemplateResponse
from app.config import settings
from app.utils.helpers import get_flashed_messages

class AppJinjaTemplates(Jinja2Templates):
    """
    Subclass that provides backwards and forwards compatibility between
    Starlette's older TemplateResponse(name, context) and modern
    TemplateResponse(request, name, context) signatures.
    """
    def TemplateResponse(self, *args, **kwargs) -> _TemplateResponse:
        # Determine arguments
        if args and isinstance(args[0], str):
            name = args[0]
            context = args[1] if len(args) > 1 else kwargs.get("context", {})
            req = kwargs.get("request")
            if req is None and isinstance(context, dict):
                req = context.get("request")
            status_code = kwargs.get("status_code", 200)
            headers = kwargs.get("headers")
            media_type = kwargs.get("media_type")
            background = kwargs.get("background")
            return super().TemplateResponse(
                request=req,
                name=name,
                context=context,
                status_code=status_code,
                headers=headers,
                media_type=media_type,
                background=background
            )
        elif args and hasattr(args[0], "scope"):
            req = args[0]
            name = args[1] if len(args) > 1 else kwargs.get("name")
            context = args[2] if len(args) > 2 else kwargs.get("context", {})
            status_code = kwargs.get("status_code", 200)
            headers = kwargs.get("headers")
            media_type = kwargs.get("media_type")
            background = kwargs.get("background")
            return super().TemplateResponse(
                request=req,
                name=name,
                context=context,
                status_code=status_code,
                headers=headers,
                media_type=media_type,
                background=background
            )
        return super().TemplateResponse(*args, **kwargs)

templates = AppJinjaTemplates(directory=str(settings.TEMPLATES_DIR))

# Custom filters
def format_date(value, fmt="%b %d, %Y"):
    if not value:
        return "N/A"
    if isinstance(value, (date, datetime)):
        return value.strftime(fmt)
    try:
        parsed = datetime.strptime(str(value), "%Y-%m-%d")
        return parsed.strftime(fmt)
    except Exception:
        return str(value)

def format_currency(value):
    try:
        val = float(value)
        return f"${val:.2f}"
    except (ValueError, TypeError):
        return "$0.00"

templates.env.filters["format_date"] = format_date
templates.env.filters["currency"] = format_currency

# Global functions accessible inside all Jinja templates
templates.env.globals["get_flashed_messages"] = get_flashed_messages
templates.env.globals["app_settings"] = settings
templates.env.globals["current_date"] = date.today

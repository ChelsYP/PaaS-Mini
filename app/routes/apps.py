from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app import auth, config

router = APIRouter()
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user: dict = Depends(auth.require_login)):
    """Halaman Beranda / Daftar Aplikasi (FR-10)."""
    # Pada Tahap 1, daftar aplikasi kosong; akan diintegrasikan dengan Docker & DB di Tahap 2 & 3.
    apps = []
    return templates.TemplateResponse(
        request,
        "apps_list.html",
        {
            "user": user,
            "apps": apps,
            "max_apps": config.MAX_APPS_PER_USER
        }
    )


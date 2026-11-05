from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app import auth, db, config

router = APIRouter(prefix="/users")
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def list_users_page(request: Request, user: dict = Depends(auth.require_admin)):
    """Halaman Manajemen Pengguna (Admin Only - FR-14)."""
    users = db.list_users()
    return templates.TemplateResponse(
        request,
        "users.html",
        {
            "user": user,
            "users": users
        }
    )

@router.post("", response_class=RedirectResponse)
@router.post("/", response_class=RedirectResponse)
async def create_user_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    user: dict = Depends(auth.require_admin)
):
    """Buat pengguna baru oleh admin."""
    username = username.strip()
    if not username or len(password) < 6:
        raise HTTPException(status_code=400, detail="Data pengguna tidak valid.")
    
    existing = db.get_user_by_username(username)
    if existing:
        raise HTTPException(status_code=400, detail="Username sudah digunakan.")
        
    pwd_hash = auth.hash_password(password)
    db.create_user(username, pwd_hash, role)
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{user_id}/delete", response_class=RedirectResponse)
async def delete_user_action(
    user_id: int,
    request: Request,
    user: dict = Depends(auth.require_admin)
):
    """Hapus pengguna oleh admin (kecuali akun sendiri)."""
    if user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus akun sendiri.")
    db.delete_user(user_id)
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


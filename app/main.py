from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config, db, auth
from app.routes.apps import router as apps_router
from app.routes.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inisialisasi database SQLite dan akun admin awal
    db.init_db()
    db.seed_admin_user(auth.hash_password)
    yield

app = FastAPI(
    title="PaaS Mini Dashboard",
    description="Dashboard mandiri berbasis container Docker + NPM",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware Session Cookie
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    session_cookie="paas_session",
    same_site="lax",
    https_only=False
)

templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

# Custom Exception Handler untuk penanganan Redirect dan Unauthorized
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_303_SEE_OTHER:
        location = exc.headers.get("Location", "/login") if exc.headers else "/login"
        return RedirectResponse(url=location, status_code=status.HTTP_303_SEE_OTHER)
    
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        if request.headers.get("HX-Request") == "true":
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={},
                headers={"HX-Redirect": "/login"}
            )
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if exc.status_code == status.HTTP_403_FORBIDDEN:
        return HTMLResponse(
            content=f"<div style='font-family: monospace; padding: 2rem; background: #09090b; color: #f43f5e;'>"
                    f"<h2>403 - Akses Ditolak</h2><p>{exc.detail}</p><a href='/' style='color: #818cf8;'>Kembali ke Beranda</a></div>",
            status_code=status.HTTP_403_FORBIDDEN
        )

    return HTMLResponse(
        content=f"<div style='font-family: monospace; padding: 2rem; background: #09090b; color: #e4e4e7;'>"
                f"<h2>{exc.status_code} Error</h2><p>{exc.detail}</p><a href='/' style='color: #818cf8;'>Kembali</a></div>",
        status_code=exc.status_code
    )

# ----------------- ENDPOINT HEALTHZ -----------------
@app.get("/healthz")
async def healthz():
    """Endpoint cek kesehatan sistem (tanpa login - NFR)."""
    return {
        "status": "ok",
        "app": "paas-dashboard",
        "database": "connected"
    }

# ----------------- AUTENTIKASI (FR-11) -----------------
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Halaman Form Login."""
    current_user = auth.get_current_user(request)
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "login.html", {"user": None, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Proses validasi login pengguna."""
    user = db.get_user_by_username(username.strip())
    
    # Validasi user dan hash password
    if not user or not auth.verify_password(password, user["password_hash"]):
        # Pesan ramah tanpa membocorkan eksistensi username
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "user": None,
                "error": "Nama pengguna atau kata sandi tidak valid."
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Simpan session login
    request.session["user_id"] = user["id"]
    request.session["username"] = user["username"]
    request.session["role"] = user["role"]
    
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/logout")
async def logout_action(request: Request):
    """Proses keluar dan pembersihan session."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

# ----------------- REGISTRASI ROUTERS -----------------
app.include_router(apps_router)
app.include_router(users_router)


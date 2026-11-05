import bcrypt
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
from app import db

def hash_password(password: str) -> str:
    """Hash password menggunakan bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifikasi kecocokan password dengan hash bcrypt."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Ambil user yang sedang login dari session cookie."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    # Ambil user dari database untuk memastikan akun masih valid
    user = db.get_user_by_id(user_id)
    if not user:
        request.session.clear()
        return None
    return user

def require_login(request: Request) -> Dict[str, Any]:
    """Dependency / guard untuk memastikan pengguna sudah login."""
    user = get_current_user(request)
    if not user:
        if request.headers.get("HX-Request") == "true":
            # Jika HTMX request, arahkan browser ke login
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"HX-Redirect": "/login"}
            )
        # Jika request browser standar, redirect 303 ke /login
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    return user

def require_admin(request: Request) -> Dict[str, Any]:
    """Dependency / guard untuk memastikan pengguna memiliki peran admin."""
    user = require_login(request)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses hanya diperbolehkan untuk Administrator."
        )
    return user


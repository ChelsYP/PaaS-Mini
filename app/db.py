import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from app import config

def get_db_path() -> str:
    path = Path(config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db() -> None:
    """Inisialisasi tabel database SQLite sesuai PRD Section 6.3."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Tabel users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role          TEXT NOT NULL CHECK (role IN ('admin','user')),
            created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Tabel apps
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS apps (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT UNIQUE NOT NULL,
            owner_id       INTEGER NOT NULL REFERENCES users(id),
            image          TEXT NOT NULL,
            container_port INTEGER NOT NULL DEFAULT 80,
            env_json       TEXT NOT NULL DEFAULT '{}',
            mem_mb         INTEGER NOT NULL,
            cpu            REAL NOT NULL,
            container_name TEXT NOT NULL,
            container_id   TEXT,
            proxy_host_id  INTEGER,
            public_domain  TEXT NOT NULL,
            local_domain   TEXT NOT NULL,
            status         TEXT NOT NULL,
            error_message  TEXT,
            created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

def create_user(username: str, password_hash: str, role: str = "user") -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        conn.commit()
        return cursor.lastrowid

def list_users() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT id, username, role, created_at FROM users ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]

def delete_user(user_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0

def seed_admin_user(hash_fn) -> None:
    """Membuat akun admin default jika belum ada."""
    existing = get_user_by_username(config.ADMIN_USERNAME)
    if not existing:
        pwd_hash = hash_fn(config.ADMIN_PASSWORD)
        create_user(config.ADMIN_USERNAME, pwd_hash, role="admin")


import os
from pathlib import Path

# Basis path proyek
BASE_DIR = Path(__file__).resolve().parent.parent

# Muat file .env jika ada tanpa dependensi tambahan
env_file = BASE_DIR / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key not in os.environ:
                    os.environ[key] = val

# Konfigurasi aplikasi
SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-development-key-change-in-prod")
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "adminpassword123")

# Nginx Proxy Manager (NPM)
NPM_URL: str = os.getenv("NPM_URL", "http://npm:81").rstrip("/")
NPM_EMAIL: str = os.getenv("NPM_EMAIL", "admin@example.com")
NPM_PASSWORD: str = os.getenv("NPM_PASSWORD", "changeme")

# Docker & Domains
DOCKER_NETWORK: str = os.getenv("DOCKER_NETWORK", "npm_default")
PUBLIC_DOMAIN: str = os.getenv("PUBLIC_DOMAIN", "chelsa.me")
LOCAL_DOMAIN: str = os.getenv("LOCAL_DOMAIN", "paas.local")

# Alokasi Resource
DEFAULT_MEM_MB: int = int(os.getenv("DEFAULT_MEM_MB", "256"))
DEFAULT_CPU: float = float(os.getenv("DEFAULT_CPU", "0.5"))
MAX_APPS_PER_USER: int = int(os.getenv("MAX_APPS_PER_USER", "5"))

# Database SQLite
DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "data" / "paas.db"))

# Templates Directory
TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"



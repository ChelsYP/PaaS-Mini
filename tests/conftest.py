import pytest
import tempfile
import os
from pathlib import Path
from starlette.testclient import TestClient

# Pastikan path modul terbaca
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, db, auth

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Set database sementara untuk isolasi pengujian."""
    test_db_file = tmp_path / "test_paas.db"
    monkeypatch.setattr(config, "DB_PATH", str(test_db_file))
    
    # Inisialisasi DB dan seed admin
    db.init_db()
    db.seed_admin_user(auth.hash_password)
    
    yield test_db_file
    
    if test_db_file.exists():
        try:
            test_db_file.unlink()
        except Exception:
            pass

@pytest.fixture
def client():
    """Test client untuk FastAPI app."""
    from app.main import app
    with TestClient(app, follow_redirects=False) as c:
        yield c


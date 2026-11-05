from app import auth, db, config

def test_password_hashing():
    """Uji fungsi bcrypt hashing dan verifikasi."""
    raw = "rahasia123"
    hashed = auth.hash_password(raw)
    assert hashed != raw
    assert auth.verify_password(raw, hashed) is True
    assert auth.verify_password("salah", hashed) is False

def test_admin_seeding():
    """Uji apakah akun admin awal berhasil dibuat secara otomatis."""
    admin = db.get_user_by_username(config.ADMIN_USERNAME)
    assert admin is not None
    assert admin["role"] == "admin"
    assert auth.verify_password(config.ADMIN_PASSWORD, admin["password_hash"]) is True

def test_unauthenticated_redirect_to_login(client):
    """Pengujian FR-11: Akses ke / saat belum login harus dialihkan ke /login."""
    response = client.get("/")
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

def test_login_failure(client):
    """Pengujian FR-11: Login dengan password salah menghasilkan status 401 dan pesan error."""
    response = client.post(
        "/login",
        data={"username": config.ADMIN_USERNAME, "password": "passwordsalah"}
    )
    assert response.status_code == 401
    assert "Nama pengguna atau kata sandi tidak valid" in response.text

def test_login_success_and_access(client):
    """Pengujian FR-11: Login berhasil menyimpan session dan dapat membuka halaman beranda."""
    response = client.post(
        "/login",
        data={"username": config.ADMIN_USERNAME, "password": config.ADMIN_PASSWORD}
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    
    # Session cookie harus terpasang
    cookie = response.cookies.get("paas_session")
    assert cookie is not None

    # Buka halaman beranda dengan session
    home_res = client.get("/", cookies={"paas_session": cookie})
    assert home_res.status_code == 200
    assert "PaaS Mini" in home_res.text
    assert config.ADMIN_USERNAME in home_res.text

def test_logout(client):
    """Pengujian FR-11: Logout menghapus session dan mengalihkan ke /login."""
    login_res = client.post(
        "/login",
        data={"username": config.ADMIN_USERNAME, "password": config.ADMIN_PASSWORD}
    )
    cookie = login_res.cookies.get("paas_session")
    
    logout_res = client.post("/logout", cookies={"paas_session": cookie})
    assert logout_res.status_code == 303
    assert logout_res.headers["location"] == "/login"

def test_user_management_by_admin(client):
    """Pengujian FR-14: Admin dapat membuat user baru dan melihat daftar user."""
    # Login sebagai admin
    login_res = client.post(
        "/login",
        data={"username": config.ADMIN_USERNAME, "password": config.ADMIN_PASSWORD}
    )
    cookie = login_res.cookies.get("paas_session")

    # Tambah user biasa baru
    create_res = client.post(
        "/users",
        data={"username": "mhs1", "password": "mhs1password", "role": "user"},
        cookies={"paas_session": cookie}
    )
    assert create_res.status_code == 303

    # Cek daftar user
    users_res = client.get("/users", cookies={"paas_session": cookie})
    assert users_res.status_code == 200
    assert "mhs1" in users_res.text

    # Uji login sebagai user baru
    mhs_login = client.post(
        "/login",
        data={"username": "mhs1", "password": "mhs1password"}
    )
    assert mhs_login.status_code == 303
    mhs_cookie = mhs_login.cookies.get("paas_session")

    # User biasa TIDAK boleh bisa mengakses /users (FR-14)
    forbidden_res = client.get("/users", cookies={"paas_session": mhs_cookie})
    assert forbidden_res.status_code == 403


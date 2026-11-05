# PRD: Dashboard PaaS Mini (Docker + Nginx Proxy Manager + Bind9 + Cloudflare Tunnel)

> Dokumen ini ditulis untuk dua pembaca: dosen (sebagai PRD projek) dan **AI coding agent** (sebagai spesifikasi yang bisa langsung dikerjakan).
> Bagian 1-4 memberi konteks, bagian 5 ke bawah adalah spesifikasi build.

---

## 1. Ringkasan Produk

**Nama:** PaaS Mini Kelompok (dashboard: `paas-dashboard`)

**Satu kalimat:** Platform hosting mandiri berbasis container. Pengguna mengisi form di dashboard untuk menjalankan aplikasi web dari image Docker, lalu aplikasi otomatis mendapat domain lokal dan domain publik.

**Masalah:** Mahasiswa dan pengembang pemula butuh tempat menjalankan aplikasi web tanpa biaya hosting dan tanpa keahlian server.

**Solusi:** Dashboard web yang mengotomatisasi tiga hal yang tadinya manual: membuat container, mendaftarkan domain di Nginx Proxy Manager (NPM), dan mengelola siklus hidup aplikasi (start, stop, log, hapus).

**Pengguna:**

| Peran | Kebutuhan |
|---|---|
| Admin (kelompok) | Membuat akun pengguna, melihat semua aplikasi, memantau resource |
| Pengguna | Membuat, menjalankan, dan menghapus aplikasi miliknya sendiri |
| Pengunjung | Membuka aplikasi lewat domain publik atau lokal |

---

## 2. Status Saat Ini (sudah berjalan, jangan dibangun ulang)

Infrastruktur berikut sudah terpasang dan teruji di VM. Dashboard hanya **memakai** komponen ini.

| Komponen | Detail |
|---|---|
| VM | Ubuntu Server di VirtualBox, 2 core, RAM 2-3 GB, disk root 23 GB |
| Jaringan VM | Adapter 1 host-only `192.168.56.10/24` (statis), Adapter 2 NAT (DHCP, internet) |
| Bind9 | Zona `paas.local`, wildcard `*.paas.local` mengarah ke `192.168.56.10` |
| Docker | Docker Engine + Compose v2 |
| Portainer CE | Port `9443` (hanya akses lokal) |
| Nginx Proxy Manager | Container `npm`, admin UI port `81`, proxy port `80` dan `443`, network Docker `npm_default` |
| Cloudflare Tunnel | Named tunnel `paas-tunnel` (service systemd `cloudflared`), wildcard `*.chelsa.me` diteruskan ke `http://localhost:80` |
| Aplikasi contoh manual | Container `app1` dan `app2` (nginx:alpine). **Bukan** milik dashboard, abaikan |
| Nginx lama (Cloud PBX, Zabbix) | Berjalan di port `8080`, `8081`, `8443`. Tidak boleh disentuh |

Domain publik: `chelsa.me`. Domain lokal: `paas.local`.

---

## 3. Arsitektur

### 3.1 Diagram komponen

```
                 Pengguna Internet                     Pengguna di laptop (host-only)
                        |                                          |
                        v                                          v
        Cloudflare DNS + Proxy (*.chelsa.me)           Bind9 @ 192.168.56.10:53
                        |                                (*.paas.local -> 192.168.56.10)
                        v                                          |
        Cloudflare Tunnel (service cloudflared)                    |
                        |  http://localhost:80                     |
                        +--------------------+---------------------+
                                             v
                          Nginx Proxy Manager (container `npm`)
                          :80 / :443 (proxy)   :81 (admin API, internal)
                                             |
            +--------------------+-----------+-----------+--------------------+
            v                    v                       v                    v
   paas-dashboard         paas-<app-A>             paas-<app-B>            app1 / app2
   (FastAPI :8000)        (container user)         (container user)       (manual, diabaikan)

   Semua container berada di Docker network `npm_default`.
   paas-dashboard mengakses:  Docker Engine (/var/run/docker.sock)  dan  NPM API (http://npm:81)
```

### 3.2 Aturan akses (penting untuk keamanan)

| Layanan | Akses lokal (`paas.local`) | Akses publik (`chelsa.me`) |
|---|---|---|
| Dashboard | `dashboard.paas.local` | **Tidak** (jangan buat Proxy Host publik) |
| Portainer | `https://192.168.56.10:9443` | **Tidak** |
| NPM admin | `http://192.168.56.10:81` | **Tidak** |
| Aplikasi pengguna | `nama.paas.local` | `nama.chelsa.me` |

Karena wildcard `*.chelsa.me` masuk ke NPM, subdomain tanpa Proxy Host hanya menghasilkan 404. Dashboard **tidak boleh** pernah membuat Proxy Host untuk nama yang dicadangkan (lihat 6.2).

### 3.3 Alur "Buat Aplikasi"

```
Pengguna            Dashboard (backend)              Docker Engine          NPM API
   | isi form            |                                 |                    |
   |-------------------->| 1. validasi input               |                    |
   |                     | 2. cek nama unik + tidak reserved                    |
   |                     | 3. pull image  --------------->|                    |
   |                     | 4. create+start container ----->|                    |
   |                     |    (network npm_default, limit, label)               |
   |                     | 5. login NPM (token) ------------------------------>|
   |                     | 6. POST /nginx/proxy-hosts ------------------------>|
   |                     |    domain: nama.chelsa.me + nama.paas.local          |
   |                     |    forward: paas-nama:port                           |
   |                     | 7. simpan ke SQLite, status=running                  |
   |<--------------------| 8. tampilkan link publik + lokal                     |
   |
   Jika langkah 4-7 gagal: ROLLBACK (hapus Proxy Host, hapus container), status=failed, tampilkan pesan error.
```

---

## 4. Ruang Lingkup

**Termasuk:**
- Dashboard web (login, daftar aplikasi, buat aplikasi, detail aplikasi, log, statistik).
- Otomasi container (Docker SDK) dan Proxy Host (NPM API).
- Manajemen pengguna sederhana (admin dan pengguna).

**Di luar lingkup:** build dari source code (buildpack), deploy dari Git, auto-scaling, multi-node, billing, sertifikat SSL per aplikasi (HTTPS publik sudah ditangani Cloudflare), volume persisten dari host.

---

## 5. Kebutuhan Fungsional

FR-01 sampai FR-07 adalah kebutuhan infrastruktur dan **sudah terpenuhi**. FR-08 sampai FR-14 adalah **target build** untuk agent.

### 5.1 Infrastruktur (terpenuhi)

| Kode | Kebutuhan | Status |
|---|---|---|
| FR-01 | `*.paas.local` diresolusi ke IP server oleh Bind9 | Selesai |
| FR-02 | Container dapat dikelola lewat Portainer | Selesai |
| FR-03 | Domain dapat dihubungkan ke container lewat NPM | Selesai |
| FR-04 | Aplikasi diakses lewat nama domain | Selesai |
| FR-05 | Aplikasi dapat diakses publik lewat Cloudflare Tunnel | Selesai |
| FR-06 | Log dan resource container dapat dilihat | Selesai (Portainer) |
| FR-07 | CPU dan RAM container dapat dibatasi | Selesai (Portainer) |

### 5.2 Dashboard (target build)

| Kode | Kebutuhan | Prioritas |
|---|---|---|
| FR-08 | Pengguna dapat membuat aplikasi baru lewat form (nama, image, port, environment variable). | Must |
| FR-09 | Sistem otomatis membuat Proxy Host di NPM dengan dua domain: `nama.chelsa.me` dan `nama.paas.local`. | Must |
| FR-10 | Pengguna dapat melihat daftar aplikasi beserta status, domain, dan resource, serta start, stop, restart, dan hapus. | Must |
| FR-11 | Dashboard hanya dapat diakses setelah login. | Must |
| FR-12 | Pengguna dapat melihat log container (tail dan refresh). | Must |
| FR-13 | Pengguna dapat melihat statistik CPU dan RAM per aplikasi. | Should |
| FR-14 | Admin dapat membuat dan menghapus akun pengguna; pengguna biasa hanya melihat aplikasinya sendiri. | Should |

---

## 6. Spesifikasi Teknis

### 6.1 Stack (default, boleh diganti agent bila ada alasan kuat)

| Lapisan | Pilihan | Alasan |
|---|---|---|
| Backend | Python 3.12 + FastAPI + Uvicorn | Ringan, cepat dibuat |
| Docker | library `docker` (docker-py) | Mengakses `docker.sock` |
| HTTP client NPM | `httpx` | Sederhana |
| Database | SQLite (file di `/data/paas.db`) | Tanpa server tambahan, hemat RAM |
| Auth | Session cookie (itsdangerous/Starlette SessionMiddleware) + hash `bcrypt` | Sederhana dan aman |
| Frontend | Jinja2 + HTMX + Tailwind (CDN) | Tanpa build chain, ringan |
| Kemasan | Satu Dockerfile (`python:3.12-slim`) | Image kecil |

Batasan resource: dashboard harus berjalan wajar di VM RAM 2-3 GB. Hindari Node build chain, ORM berat, atau database server terpisah.

### 6.2 Aturan bisnis

- **Nama aplikasi:** regex `^[a-z][a-z0-9-]{2,30}$`, unik di database.
- **Nama dicadangkan (ditolak):** `npm`, `portainer`, `dashboard`, `www`, `app1`, `app2`, `admin`, `api`, `zabbix`, `cloudpbx`, `ns1`, `mail`.
- **Nama container:** `paas-<nama>`. NPM meneruskan ke `paas-<nama>:<port>` lewat network `npm_default`.
- **Port container:** angka 1-65535 (default `80`). Tidak ada port yang dipublish ke host (`-p` dilarang).
- **Limit default:** RAM `256 MB`, CPU `0.5` core. Admin dapat mengubah default lewat env.
- **Kuota:** maksimal `MAX_APPS_PER_USER` aplikasi per pengguna (default 5). Admin tanpa batas.
- **Label Docker** pada setiap container buatan dashboard:
  - `paas.managed=true`
  - `paas.app=<nama>`
  - `paas.owner=<username>`
  - Dashboard **hanya** mengelola container berlabel `paas.managed=true`. Container lain (portainer, npm, app1, app2) tidak boleh ditampilkan atau diubah.
- **Pembatasan keamanan container:** tanpa `privileged`, tanpa `network_mode=host`, tanpa bind mount dari host, tanpa `cap_add`. Pengguna hanya boleh memilih image, port, dan environment variable.
- **Status:** `creating`, `running`, `stopped`, `failed`. Status ditampilkan dari kondisi live Docker; kolom di database hanya cache.

### 6.3 Model data (SQLite)

```sql
CREATE TABLE users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL CHECK (role IN ('admin','user')),
  created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE apps (
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
```

Pada start-up: buat tabel jika belum ada, lalu buat akun admin dari `ADMIN_USERNAME` dan `ADMIN_PASSWORD` kalau belum ada.

### 6.4 Konfigurasi (environment variable)

| Variabel | Contoh | Keterangan |
|---|---|---|
| `SECRET_KEY` | string acak panjang | Penanda session |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | `admin` / (kuat) | Akun admin awal |
| `NPM_URL` | `http://npm:81` | Alamat NPM dari dalam network Docker |
| `NPM_EMAIL` / `NPM_PASSWORD` | akun admin NPM | Dipakai untuk mengambil token API |
| `DOCKER_NETWORK` | `npm_default` | Network tempat container aplikasi dijalankan |
| `PUBLIC_DOMAIN` | `chelsa.me` | Domain publik |
| `LOCAL_DOMAIN` | `paas.local` | Domain lokal (Bind9) |
| `DEFAULT_MEM_MB` | `256` | Limit RAM default |
| `DEFAULT_CPU` | `0.5` | Limit CPU default |
| `MAX_APPS_PER_USER` | `5` | Kuota aplikasi |
| `DB_PATH` | `/data/paas.db` | Lokasi SQLite |

Semua rahasia hanya dari environment atau file `.env` (jangan hardcode, jangan commit).

### 6.5 Integrasi Nginx Proxy Manager API

Semua dipanggil dari backend, tidak pernah dari browser.

1. **Token:** `POST {NPM_URL}/api/tokens` dengan body `{"identity": NPM_EMAIL, "secret": NPM_PASSWORD}` menghasilkan `{"token": "..."}`. Kirim sebagai header `Authorization: Bearer <token>`. Simpan token di memori dan ambil ulang saat menerima 401.
2. **Buat Proxy Host:** `POST {NPM_URL}/api/nginx/proxy-hosts` dengan body:
```json
{
  "domain_names": ["nama.chelsa.me", "nama.paas.local"],
  "forward_scheme": "http",
  "forward_host": "paas-nama",
  "forward_port": 80,
  "access_list_id": 0,
  "certificate_id": 0,
  "ssl_forced": false,
  "caching_enabled": false,
  "block_exploits": true,
  "advanced_config": "",
  "allow_websocket_upgrade": false,
  "http2_support": false,
  "hsts_enabled": false,
  "hsts_subdomains": false,
  "meta": {"letsencrypt_agree": false, "dns_challenge": false},
  "locations": []
}
```
   Simpan `id` dari respons ke `apps.proxy_host_id`.
3. **Hapus:** `DELETE {NPM_URL}/api/nginx/proxy-hosts/{proxy_host_id}`.
4. **Catatan:** skema field bisa sedikit berbeda antar versi NPM. Agent wajib memverifikasi ke instance NPM yang berjalan (misalnya `GET {NPM_URL}/api/schema` bila tersedia, atau menguji dengan `curl`) dan menyesuaikan body bila ada penolakan validasi. Bungkus semua pemanggilan NPM dalam satu modul `npm_client.py` agar mudah diperbaiki.

### 6.6 Integrasi Docker

- Klien: `docker.from_env()` (socket di `/var/run/docker.sock`).
- Pull image dengan timeout; tangani image tidak ditemukan dan pesan error yang ramah.
- `containers.run(..., detach=True, name="paas-<nama>", network=DOCKER_NETWORK, restart_policy={"Name": "unless-stopped"}, mem_limit=f"{mem}m", nano_cpus=int(cpu*1e9), environment=env, labels=labels)`.
- Log: `container.logs(tail=200, timestamps=True)`.
- Statistik: `container.stats(stream=False)`, hitung persen CPU dan pemakaian RAM dari respons.
- Penghapusan: stop, remove container, lalu hapus Proxy Host, lalu hapus baris database. Image tidak ikut dihapus.

### 6.7 Endpoint

| Method | Path | Fungsi | FR |
|---|---|---|---|
| GET | `/login` | Halaman login | FR-11 |
| POST | `/login` | Proses login | FR-11 |
| POST | `/logout` | Keluar | FR-11 |
| GET | `/` | Daftar aplikasi | FR-10 |
| GET | `/apps/new` | Form buat aplikasi | FR-08 |
| POST | `/apps` | Buat aplikasi (alur 3.3) | FR-08, FR-09 |
| GET | `/apps/{id}` | Detail aplikasi (tab ringkasan, log, environment) | FR-10 |
| POST | `/apps/{id}/start` | Jalankan | FR-10 |
| POST | `/apps/{id}/stop` | Hentikan | FR-10 |
| POST | `/apps/{id}/restart` | Mulai ulang | FR-10 |
| POST | `/apps/{id}/delete` | Hapus (butuh konfirmasi) | FR-10 |
| GET | `/apps/{id}/logs` | Fragmen log (HTMX, dapat dipolling) | FR-12 |
| GET | `/apps/{id}/stats` | Fragmen statistik CPU dan RAM | FR-13 |
| GET | `/users` | Daftar pengguna (admin) | FR-14 |
| POST | `/users` | Buat pengguna (admin) | FR-14 |
| POST | `/users/{id}/delete` | Hapus pengguna (admin) | FR-14 |
| GET | `/healthz` | Cek kesehatan (tanpa login) | NFR |

Semua endpoint selain `/login` dan `/healthz` wajib login. Pengguna biasa hanya boleh mengakses aplikasi miliknya (cek `owner_id`, balas 404 bila bukan miliknya). Aksi yang mengubah data memakai POST (bukan GET) dan dilindungi token CSRF sederhana atau header yang dicek.

### 6.8 Struktur proyek yang disarankan

```
paas-dashboard/
├── app/
│   ├── main.py            # FastAPI app, middleware, router
│   ├── config.py          # baca environment variable
│   ├── db.py              # koneksi SQLite + inisialisasi tabel
│   ├── auth.py            # login, session, dependency require_login/require_admin
│   ├── docker_client.py   # semua akses Docker
│   ├── npm_client.py      # semua akses NPM API
│   ├── services.py        # alur create/delete app + rollback
│   ├── routes/
│   │   ├── apps.py
│   │   └── users.py
│   └── templates/         # base.html, login.html, apps_list.html, app_new.html, app_detail.html, users.html
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### 6.9 Deploy dashboard (docker-compose.yml)

```yaml
services:
  dashboard:
    build: .
    container_name: paas-dashboard
    restart: unless-stopped
    env_file: .env
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/data
    networks:
      - npm_default

networks:
  npm_default:
    external: true
```

Setelah container berjalan, daftarkan **secara manual** satu Proxy Host di NPM: domain `dashboard.paas.local`, forward ke `paas-dashboard:8000`. Jangan tambahkan domain `chelsa.me`.

Catatan: akses ke `docker.sock` dari dalam container butuh izin. Agent boleh menjalankan proses sebagai root di container atau menambahkan grup `docker` dengan GID dari host; pilih yang paling sederhana dan dokumentasikan di README.

---

## 7. UI/UX

Bahasa antarmuka: **Bahasa Indonesia**. Pola mengikuti dashboard PaaS populer (Vercel, Railway, Render, Heroku).

**Halaman:**

1. **Login:** form di tengah layar.
2. **Daftar aplikasi (beranda):** kartu atau tabel berisi nama, lencana status berwarna, tautan domain publik dan lokal yang dapat diklik, dan tombol aksi. Tombol **Buat Aplikasi** di kanan atas. Tampilan kosong yang ramah ("Belum ada aplikasi, buat yang pertama").
3. **Buat aplikasi:** form satu halaman atau tiga langkah: (1) nama dan image, (2) port dan environment variable (tambah baris dinamis), (3) ringkasan domain yang akan dibuat. Tampilkan progres saat membuat: *Mengunduh image, Membuat container, Membuat domain, Aktif*.
4. **Detail aplikasi:** tab **Ringkasan** (status, domain, image, limit, statistik), **Log** (font monospace, latar gelap, refresh otomatis tiap beberapa detik), **Environment** (nilai disamarkan, tombol tampilkan), **Pengaturan** (tombol hapus dengan konfirmasi).
5. **Pengguna (admin):** tabel pengguna dan form tambah.

**Aturan tampilan:**
- Warna status konsisten: hijau (running), kuning (creating), merah (failed), abu-abu (stopped).
- Dialog konfirmasi sebelum hapus; notifikasi singkat setelah setiap aksi.
- Satu warna aksen, banyak ruang kosong, responsif sampai lebar ponsel, dukungan mode gelap bila mudah.
- Pesan error harus spesifik dan ramah (misalnya "Image `foo/bar` tidak ditemukan di Docker Hub").

---

## 8. Kebutuhan Non-Fungsional

| Aspek | Kebutuhan |
|---|---|
| Performa | Halaman daftar terbuka di bawah 2 detik; pembuatan aplikasi dengan image ringan selesai di bawah 60 detik (di luar waktu pull) |
| Resource | Dashboard memakai RAM di bawah 150 MB saat idle |
| Keamanan | Hash password `bcrypt`; session cookie `HttpOnly` dan `SameSite=Lax`; pembatasan percobaan login; validasi semua input; rahasia hanya dari environment; dashboard tidak dipublikasikan ke internet |
| Ketahanan | Rollback otomatis bila pembuatan gagal; container aplikasi memakai `restart: unless-stopped`; dashboard aktif lagi setelah VM restart |
| Portabilitas | Seluruh konfigurasi lewat environment variable, tanpa path atau IP hardcode |
| Kemudahan | Membuat aplikasi tanpa mengetik perintah |

---

## 9. Kriteria Penerimaan (Acceptance Criteria)

**FR-11 (login):**
- Diberikan pengguna belum login, ketika membuka `/`, maka diarahkan ke `/login`.
- Diberikan kredensial benar, ketika login, maka masuk ke beranda. Kredensial salah menampilkan pesan error tanpa membocorkan apakah username ada.

**FR-08 dan FR-09 (buat aplikasi):**
- Diberikan nama `demo`, image `nginx:alpine`, port `80`, ketika form dikirim, maka container `paas-demo` berjalan di network `npm_default`, Proxy Host dibuat di NPM, dan halaman menampilkan `demo.chelsa.me` dan `demo.paas.local`.
- Setelah itu `http://demo.paas.local` (dari laptop) dan `https://demo.chelsa.me` (dari jaringan lain) menampilkan halaman nginx.
- Diberikan nama sudah dipakai atau termasuk nama dicadangkan, maka ditolak dengan pesan jelas dan tidak ada container yang dibuat.
- Diberikan image tidak ada, maka status `failed`, tidak ada container atau Proxy Host tersisa.
- Bila pembuatan Proxy Host gagal, container yang sudah dibuat dihapus (rollback).

**FR-10 (kelola):**
- Daftar hanya menampilkan container berlabel `paas.managed=true`. `portainer`, `npm`, `app1`, `app2` tidak muncul.
- Stop mengubah status menjadi `stopped` dan domain menampilkan 502; start mengembalikan ke `running`.
- Hapus (setelah konfirmasi) menghapus container, Proxy Host, dan baris database; domain kembali menghasilkan 404.

**FR-12 dan FR-13:**
- Tab Log menampilkan 200 baris terakhir dan dapat dimuat ulang.
- Statistik menampilkan persen CPU dan pemakaian RAM terhadap limit.

**FR-14:**
- Pengguna biasa tidak dapat melihat atau mengakses aplikasi pengguna lain (404). Admin melihat semua. Hanya admin yang dapat membuka `/users`.

---

## 10. Urutan Pengerjaan untuk Agent

Kerjakan bertahap; setiap tahap harus dapat dijalankan dan diuji sebelum lanjut.

1. **Kerangka dan auth:** struktur proyek, config, SQLite, login/logout, akun admin awal, halaman kosong, `/healthz`, Dockerfile dan compose.
2. **Docker dan daftar aplikasi:** `docker_client.py`, daftar container berlabel, start/stop/restart/hapus container (tanpa NPM dulu).
3. **Buat aplikasi + NPM:** `npm_client.py`, alur 3.3 lengkap dengan rollback dan validasi nama.
4. **Log dan statistik:** endpoint fragmen HTMX, tab detail aplikasi.
5. **Pengguna dan kepemilikan:** FR-14, kuota, pembatasan akses per pemilik.
6. **Poles dan dokumentasi:** UI sesuai bagian 7, pesan error, `README.md` (cara build, `.env`, daftarkan `dashboard.paas.local` di NPM), tes dasar.

Di setiap tahap, jalankan tes mandiri (pytest dengan Docker dan NPM di-mock untuk logika; uji manual terhadap VM nyata untuk integrasi) dan laporkan apa yang diuji.

---

## 11. Aturan untuk Agent

- Jangan mengubah atau menampilkan container yang tidak berlabel `paas.managed=true`.
- Jangan menjalankan perintah yang memodifikasi Bind9, Cloudflare, Nginx lama, atau Portainer; semuanya sudah selesai.
- Jangan menyimpan rahasia di kode atau repositori; sediakan `.env.example` saja.
- Jangan membuka port tambahan di host dan jangan membuat Proxy Host publik untuk dashboard, Portainer, atau NPM admin.
- Bila skema NPM API berbeda dari contoh di 6.5, sesuaikan di `npm_client.py` dan catat di README.
- Bila ada keputusan yang belum jelas, pilih opsi paling sederhana yang memenuhi FR dan catat asumsinya di README.

---

## 12. Risiko

| Risiko | Mitigasi |
|---|---|
| Akses `docker.sock` setara akses root | Login wajib, dashboard hanya lokal, pembatasan opsi container (6.2), tanpa akses publik |
| Skema NPM API berbeda antar versi | Modul klien terpisah, verifikasi ke instance nyata |
| RAM VM terbatas | Limit default per container, kuota per pengguna, stack ringan |
| Image besar membuat pull lambat atau disk penuh | Tampilkan progres, batasi jumlah aplikasi, admin dapat membersihkan image |
| Laptop atau VM mati saat demo | Snapshot VM, tunnel berjalan sebagai service, siapkan rekaman layar cadangan |

---

## 13. Skenario Demo

1. Tunjukkan `nslookup demo.paas.local` ke Bind9.
2. Login ke `dashboard.paas.local`, tunjukkan daftar aplikasi.
3. Buat aplikasi baru lewat form (misalnya `nginx:alpine`), tunjukkan progresnya.
4. Buka `demo.paas.local` di laptop dan `demo.chelsa.me` dari HP dengan data seluler.
5. Tunjukkan log dan statistik, lalu stop dan hapus aplikasi.
6. Tunjukkan bahwa domain kembali tidak aktif.

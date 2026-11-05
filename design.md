Tolong buatkan rancangan dan antarmuka UI/UX (Frontend) untuk aplikasi "Dashboard PaaS Mini" berdasarkan spesifikasi PRD berikut. 

### 🚫 STRICT NO AI SLOP RULES (Aturan Tampilan Utama):
1. DILARANG menggunakan efek "AI Slop" seperti: hero gradient warna-warni yang berlebihan, latar belakang berpola mesh/glow yang tidak perlu, teks tagline pemasaran yang muluk-muluk, animasi floating card yang kekanak-kanakan, atau ilustrasi 3D generik.
2. Desain HARUS utilitarian, padat informasi, bersih, dan berfokus pada fungsionalitas pengembang (seperti Vercel, Railway, atau Supabase Dashboard).
3. Gunakan skema warna profesional: Latar belakang netral (Dark Mode slate/zinc atau Light Mode clean crisp), warna aksen tunggal (misal: Indigo atau Violet), serta warna status standar (Hijau = Running, Kuning = Creating, Merah = Failed, Abu-abu = Stopped).
4. Gunakan bahasa antarmuka: Bahasa Indonesia yang jelas, ringkas, dan teknis.

---

### 💻 TEKNOLOGI FRONTEND:
- Tailwind CSS (via CDN atau framework-less)
- HTMX (untuk dynamic update seperti log polling, tab switching, dan aksi tanpa reload)
- Jinja2 Templates (HTML modular)
- Font: Monospace untuk log & terminal (Inter / JetBrains Mono / Fira Code)

---

### 🎨 SPEC & RANCANGAN HALAMAN (Hanya 5 Halaman Utama):

#### 1. Halaman Login (`/login`)
- **Layout:** Centered Card minimalis di atas latar netral.
- **Elemen:**
  - Header: Logo/Nama sederhana "PaaS Mini" & Subtitle "Masuk ke Dashboard".
  - Form: Input Username, Input Password, Tombol "Masuk".
  - Pesan Error: Alert box merah sederhana jika login gagal.

#### 2. Beranda / Daftar Aplikasi (`/`)
- **Header:** Judul "Aplikasi Saya", tombol utama "+ Buat Aplikasi" (Primary Button di kanan atas), dan ringkasan kuota (contoh: "3 dari 5 aplikasi digunakan").
- **State Kosong (Empty State):** Jika belum ada aplikasi, tampilkan kotak bergaris putus-putus dengan icon minimalis & teks: "Belum ada aplikasi yang berjalan. Buat aplikasi pertama Anda."
- **Tampilan Daftar (Grid / Card List):**
  - Kartu Aplikasi memuat:
    - Nama aplikasi (bold) + Badge Status warna-warni (Running/Stopped/Failed).
    - Nama Image Docker (misal: `nginx:alpine`).
    - Dua Tautan Domain (Klik untuk buka): 
      - Publik: `https://[nama].chelsa.me`
      - Lokal: `http://[nama].paas.local`
    - Quick Actions: Tombol icon kecil untuk Start, Stop, dan Link ke Detail.

#### 3. Form Buat Aplikasi Baru (`/apps/new`)
- **Layout:** Single-page form terstruktur atau Multi-step wizard ringkas.
- **Input Fields:**
  - **Nama Aplikasi:** Input teks (dengan helper text: "Hanya huruf kecil, angka, dan tanda hubung").
  - **Docker Image:** Input teks (misal: `redis:latest` atau `nginx:alpine`).
  - **Port Container:** Input angka (default: `80`).
  - **Environment Variables:** Dynamic key-value pairs (Tombol "+ Tambah Variable", input `KEY` dan `VALUE`, tombol hapus baris).
  - **Limit Resource Info:** Tampilkan badge non-editable/read-only info (`RAM: 256MB`, `CPU: 0.5 Core`).
- **Feedback Indicator:** Tampilkan indikator status progres (Loading state) saat submit: *"Mengunduh Image... Mendaftarkan Domain... Memulai Container..."*

#### 4. Detail Aplikasi (`/apps/{id}`)
- **Header:** Nama Aplikasi, Status Badge, dan Action Buttons (Start, Stop, Restart, Hapus).
- **Tab Navigation (HTMX Powered):**
  1. **Tab Ringkasan:** Grid info berisi Status, Container ID, Image, Limit RAM/CPU, URL Publik & Lokal, dan Card ringkas Statistik CPU/RAM (grafik/bar sederhana).
  2. **Tab Log:** Dark Terminal Block (background `#0d1117`, teks monospace hijau/putih) dengan fitur Auto-scroll & Auto-refresh (HTMX polling), serta tombol "Muat Ulang Log".
  3. **Tab Environment:** Tabel pasangan Key-Value (Value disamarkan `••••••` dengan icon toggle "Tampilkan").
  4. **Tab Pengaturan (Danger Zone):** Box berbingkai merah berisi opsi "Hapus Aplikasi" dengan Modal Konfirmasi pengetikan ulang nama aplikasi sebelum dihapus.

#### 5. Manajemen Pengguna (Admin Only - `/users`)
- **Layout:** Tabel daftar pengguna (Username, Role, Tanggal Dibuat, Aksi Hapus).
- **Form Tambah Pengguna:** Form ringkas di atas/samping tabel untuk membuat user baru (Username, Password, Role: Admin/User).

---

### ⚠️ UX & BEHAVIOR ATURAN TAMBAHAN:
- **Konfirmasi Aksi Bahaya:** Semua aksi destruktif (Stop, Hapus) WAKTU memerlukan konfirmasi (modal dialog atau HTMX prompt).
- **Responsif:** Pastikan tata letak rapi dari tampilan mobile/tablet hingga desktop monitor.
- **Alert/Toast Notification:** Notifikasi toast melayang di pojok kanan atas untuk sukses/gagal aksi (misal: "Aplikasi berhasil dihentikan").

Tolong hasilkan struktur template HTML Jinja2 + kelas Tailwind CSS yang siap digunakan dan rapi.
FROM python:3.12-slim

# Mencegah penulisan berkas .pyc dan memastikan output terminal unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl untuk healthcheck di container
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Salin dependensi dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi
COPY . .

# Buat folder direktori data untuk SQLite
RUN mkdir -p /data /app/data

EXPOSE 8000

# Menjalankan server ASGI Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


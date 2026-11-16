# Restaurant & Café Management System (SaaS Multi-Tenant)

## Phase 0: Project Scaffolding, Docker & Database Foundation

### Struktur Direktori
- `backend/`: FastAPI Modular Monolith, Alembic Migrations, & Pytest suite.
- `.github/workflows/ci.yml`: Automated testing pipeline.
- `docker-compose.yml`: PostgreSQL 15 & FastAPI service.

### Cara Menjalankan & Verifikasi Phase 0
1. Salin file konfigurasi environment:
   ```bash
   cp .env.example .env
   ```
2. Jalankan PostgreSQL dan Backend via Docker Compose (otomatis menjalankan `alembic upgrade head`):
   ```bash
   docker-compose up --build -d
   ```
3. Verifikasi endpoint kesehatan & dokumentasi API:
   - Health: `http://localhost:8000/health`
   - Readiness: `http://localhost:8000/ready`
   - Swagger UI: `http://localhost:8000/api/docs`
4. Jalankan pengujian automated Pytest untuk memverifikasi 29 tabel schema PostgreSQL:
   ```bash
   docker-compose exec backend pytest -v
   ```

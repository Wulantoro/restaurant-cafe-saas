# Restaurant & Café Management System (Multi-Tenant SaaS)

A robust, enterprise-grade multi-tenant SaaS platform built for multi-outlet restaurant and café operations. Designed with a modular monolith architecture, strict tenant data isolation, and comprehensive role-based access control (RBAC).

---

## 🚀 Core Architecture & Tech Stack

- **Backend:** FastAPI (Python), SQLAlchemy ORM, Alembic Migrations
- **Database:** PostgreSQL 15 (Single-database, multi-tenant architecture with row/schema-level `tenant_id` isolation across 29 tables)
- **Containerization & CI/CD:** Docker, Docker Compose, GitHub Actions (Automated Pytest Pipeline)
- **Security & IAM:** JWT-based authentication, granular RBAC (Central Admin, Outlet Manager, Cashier, Kitchen, etc.), and immutable audit logging.

---

## 📂 Project Structure

```text
restaurant-cafe-saas/
├── backend/
│   ├── alembic/            # Database migrations
│   ├── app/
│   │   ├── core/           # Security, config, database session, exceptions
│   │   ├── models/         # SQLAlchemy ORM models (Tenants, Outlets, Users, etc.)
│   │   ├── modules/        # Domain modules (IAM, Tenants, etc.)
│   │   └── main.py         # FastAPI application entrypoint
│   └── tests/              # Automated Pytest suite (Phase 0 & Phase 1)
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml      # Local development container orchestration
└── .env.example            # Environment variables template
```

---

## 🛠️ Getting Started & Local Development

### 1. Prerequisites
- Docker & Docker Compose installed on your machine.
- Git.

### 2. Environment Configuration
Clone the repository and set up your local environment variables:
```bash
cp .env.example .env
```
*(Adjust the database credentials inside `.env` if necessary).*

### 3. Build & Run via Docker Compose
Start the PostgreSQL database and FastAPI backend services:
```bash
docker compose up --build -d
```

### 4. Verify API Health & Documentation
Once running, you can access the service endpoints:
- **Health Check:** `http://localhost:8000/health`
- **Readiness Check:** `http://localhost:8000/ready`
- **Interactive API Docs (Swagger UI):** `http://localhost:8000/api/docs`

---

## 🧪 Running Automated Tests

The project enforces strict automated testing via `pytest` inside the container to verify database integrity, tenant isolation, authentication, and permission enforcement:
```bash
docker compose exec backend pytest -v
```

---

## 📋 Development Roadmap

- [x] **Phase 0:** Project Scaffolding, Docker configuration, PostgreSQL schema migration (29 tables).
- [x] **Phase 1:** Tenancy, Outlet Management, IAM, JWT Authentication, and RBAC with strict data isolation.
- [ ] **Phase 2:** Centralized Menu, Recipes & Ingredients Management.
- [ ] **Phase 3:** Inventory Control & Multi-Outlet Stock Transfers.
- [ ] **Phase 4:** POS Workflows, Orders, & Split-Bill Logic.
- [ ] **Phase 5:** Kitchen Display System (KDS) & Real-time Operations.
- [ ] **Phase 6:** Financial Reporting, Central Admin Dashboard & Analytics.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
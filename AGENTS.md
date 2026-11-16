# AGENTS.md — Gemini Coding Agent Rules & Project Guardrails

## Restaurant & Café Management System (SaaS Multi-Tenant)

This file defines mandatory system guardrails and architectural instructions for **Gemini** when working on this repository. **You must strictly adhere to all rules below.**

## 1. Single Source of Truth

Before writing, modifying, or deleting any code, you **must read and comply with** the specification documents in the `docs/` directory:

1. `docs/Product Vision & Scope.md` (`PRD-FOUNDATION-001`) — MVP vs. Post-MVP boundaries and approved technology stack.
2. `docs/Business Requirements & Workflow.md` (`BRD-FOUNDATION-001`) — The 10 Approved Business Decisions, business actors, workflows, and business rules (`BR-001` through `BR-028`).
3. `docs/Functional & Non-Functional Requirements.md` (`FRD-FOUNDATION-001`) — Functional (`FR-001` through `FR-095`) and non-functional (`NFR-001` through `NFR-034`) specifications.
4. `docs/document_revision_pack-1.md` — Alignment revisions and **the 10 final business clarifications (`BD-001` through `BD-010`)**.
5. `docs/system_architecture_database_design.md` (`SAD-FOUNDATION-001`) — Modular Monolith architecture, transaction boundaries, and PostgreSQL DDL schema.
6. `docs/implementation_plan_api_blueprint.md` (`IMP-API-FOUNDATION-001`) — REST API contracts and phased execution roadmap.

**Hierarchy Rule:** In case of any ambiguity, the decisions in `BRD-FOUNDATION-001` and `document_revision_pack-1.md` (`BD-001`–`BD-010`) serve as the highest authoritative business rules and must never be violated.

## 2. Anti-Duplication & Strict Modularity (DRY Principle)

To prevent code duplication, redundant logic, and scattered files performing identical functions:

1. **Inspect Before Creating New Files:** Always inspect `backend/app/core/` and `backend/app/modules/` before creating any new file. Do not create new helper or utility files if the functionality already exists in `app/core/`.
2. **Reuse Existing `app/core/` Components:**
   * **Configuration:** Use `app/core/config.py` (`settings`). Never call `os.getenv()` directly across modules.
   * **Database Session:** Use `get_db` from `app/core/database.py`. Never instantiate separate database engines or sessionmakers.
   * **Security & Hashing:** Use `app/core/security.py`. Never write duplicate password hashing or JWT generation/verification functions.
   * **Error Handling:** Raise `DomainException` from `app/core/exceptions.py`. Never return ad-hoc or inconsistent JSON error structures.
   * **Logging:** Use `logging.getLogger("rcms.<module>")` configured via `app/core/logging_config.py`.
3. **One Module = One Domain Responsibility:** Place domain code strictly within the 10 pre-defined module directories under `backend/app/modules/` (`tenancy`, `iam`, `catalog`, `ordering`, `kitchen`, `pos`, `inventory`, `purchasing`, `reporting`, `audit`). Do not create new top-level module folders without explicit user instruction.
4. **Standardized File Layout per Module:** Keep each module in `backend/app/modules/<module_name>/` clean and consistent using only:
   * `models.py` (SQLAlchemy ORM models)
   * `schemas.py` (Pydantic request/response schemas)
   * `service.py` (Business logic & database transactions)
   * `router.py` (FastAPI endpoints)
   * *(Optional)* `dependencies.py` (Module-specific guards/validators)
   Do not fragment a module into dozens of tiny, overlapping files.
5. **Refactor, Never Duplicate:** If a business operation is shared across modules (such as writing to `audit_logs` or verifying outlet permissions), implement a single centralized service/guard function (`audit/service.py` or `core/permissions.py`) and import it where needed.

## 3. Strict Database & Migration Rules

1. **Database DDL is Locked:** All tables, columns, `ENUM` types, composite foreign keys `(tenant_id, id)`, and indexes defined in `backend/alembic/versions/0001_initial_foundation_schema.py` are the authoritative baseline.
2. **Do Not Alter Existing Migrations:** Never modify `0001_initial_foundation_schema.py`. All SQLAlchemy ORM models (`models.py`) must match the exact table names, column names, constraints, and types in that migration.
3. **Register All Models:** Every new `models.py` created in a module must be imported into `backend/app/models/__init__.py` so SQLAlchemy and Alembic detect all metadata properly.

## 4. Non-Negotiable Business & Security Rules

1. **Multi-Tenant Isolation (`BR-001`, `NFR-003`):**
   * Always extract `tenant_id` from the authenticated user's JWT token context—**never** trust a `tenant_id` passed in a request body or query parameter.
   * Every database `SELECT`, `UPDATE`, and `DELETE` query must explicitly filter by `tenant_id == current_user.tenant_id`.
2. **Centralized Governance vs. Outlet Scope (`BD-001`, `BR-004`–`BR-006`):**
   * `Central Admin` operates strictly within a single tenant to manage shared master data: menus, recipes (`BD-002`), pricing, tax rates, and service charge rates. Outlet staff must never be allowed to override centralized definitions or prices.
3. **Inventory Reservation & Consumption (`BR-015`–`BR-020`, `BD-003`, `BD-007`):**
   * Submitting an order to the kitchen creates `inventory_reservations` (`Available Stock = On-hand Stock - Reserved Stock`).
   * Physical stock (`on_hand_qty`) is deducted automatically based on standard centralized recipes **only when** a kitchen item transitions to `READY` (`BD-003`).
   * `Strict Inventory` is the default policy. `Allow Negative Inventory` applies only when `tenants.allow_negative_inventory == True` (authorized by the Owner) and must flag negative stock exceptions.
4. **Purchasing & Refunds (`BR-021`–`BR-024`, `BD-005`, `BD-006`, `BD-009`):**
   * Purchase Orders (POs) and Refunds strictly require `Manager` approval.
   * Once `APPROVED`, a PO is immutable (`BD-006`).
   * Physical inventory increases only upon confirmed `Goods Receiving` (`accepted_qty`).
5. **Atomic Transactions & Idempotency (`NFR-013`, `NFR-014`):**
   * Multi-step state mutations (e.g., submitting an order + reserving stock, marking an item `READY` + deducting stock, recording a payment + updating order balances) must execute inside a single atomic database transaction (`db.commit()` on success, `db.rollback()` on failure).
   * Payment creation (`POST .../payments`) must enforce `idempotency_key` uniqueness per tenant to prevent duplicate charges.
6. **Mandatory Audit Trail (`BR-027`, `FR-091`–`FR-094`):**
   * Sensitive operations—including user role/permission changes, centralized menu/price/tax updates, PO approvals/rejections, `PREPARING` order modifications, voids, refunds, waste logs, and stock adjustments—must be recorded in `audit_logs`.

## 5. Execution & Verification Workflow (Definition of Done)

1. **Execute One Phase at a Time:** Implement strictly the specific *Phase* requested by the user according to `docs/implementation_plan_api_blueprint.md`. Do not implement Post-MVP features (`PRD Section 7 & 8`).
2. **Register Routers:** Mount every implemented module's `router.py` into `backend/app/main.py` under the `/api/v1` prefix.
3. **Write & Run Pytest (`NFR-023`):**
   * Every Phase must include comprehensive automated tests in `backend/tests/test_phase<X>_<module>.py` covering happy paths, cross-tenant isolation, unauthorized role rejections, and edge cases.
   * Before concluding any task, run `pytest -v` and ensure **100% of existing and new tests pass**.
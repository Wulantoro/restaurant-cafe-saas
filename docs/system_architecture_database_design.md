# System Architecture & Database Design Document
## Restaurant & Café Management System

**Document ID:** SAD-FOUNDATION-001  
**Version:** 1.0.0  
**Status:** Approved — Technical Architecture Baseline  
**Related Documents:**
- `PRD-FOUNDATION-001` — Product Vision & Scope (v1.0.0)
- `BRD-FOUNDATION-001` — Business Requirements & Workflow (v2.0.0)
- `FRD-FOUNDATION-001` — Functional & Non-Functional Requirements (v1.0.0)
- `Document Revision Pack` — Business Clarifications (`BD-001` through `BD-010`)

---

# 1. Purpose

Dokumen ini mendefinisikan cetak biru arsitektur perangkat lunak (*System Architecture*) serta desain skema database relasional (*Entity Relationship Diagram* dan *DDL PostgreSQL*) untuk **Restaurant & Café Management System**.

Seluruh keputusan teknis dalam dokumen ini diturunkan secara ketat dari aturan bisnis yang telah disetujui pada BRD v2.0.0 dan klarifikasi final `BD-001` hingga `BD-010` tanpa mengubah atau menyimpang dari ruang lingkup MVP yang telah ditetapkan.

---

# 2. Architectural Style & Technology Stack

Mengacu pada *PRD Section 11* dan *FRD Section 4 (Non-Functional Requirements)*:

| Layer / Aspect | Technology / Pattern | Reference |
|---|---|---|
| **Architecture Pattern** | Modular Monolith | `NFR-019`, `NFR-020` |
| **Backend Language & Framework** | Python 3.11+ & FastAPI | `PRD Section 11` |
| **API Documentation** | OpenAPI 3.1 / Swagger UI (Auto-generated) | `NFR-021` |
| **Database & Migrations** | PostgreSQL 15+ & Alembic | `NFR-022`, `PRD Section 11` |
| **Frontend Web Framework** | Next.js (App Router) & TypeScript | `PRD Section 11`, `NFR-030`, `NFR-031` |
| **Automated Testing** | Pytest (Unit, Integration, Authorization, Concurrency) | `NFR-023`, `PRD Section 11` |
| **Containerization & CI/CD** | Docker & GitHub Actions | `NFR-032`, `NFR-033` |

---

# 3. Multi-Tenant & Security Architecture

Untuk memenuhi aturan isolasi bisnis (`BR-001`, `BR-002`, `BR-003`, `NFR-003`, `NFR-004`), sistem menerapkan strategi **Shared Database, Shared Schema dengan Tenant Discriminator** dan pertahanan berlapis (*Defense-in-Depth*):

1. **Tenant & Outlet Scoping di Level Token & Dependency (`NFR-004`):**
   * Setiap *authenticated request* membawa JWT yang memuat identitas `user_id` dan `tenant_id`.
   * *FastAPI Dependency* (`get_current_tenant_context`) memverifikasi status aktif pengguna, izin peran (*RBAC*), serta hak akses spesifik terhadap `outlet_id` yang diminta pada sisi backend sebelum masuk ke *service layer*.
2. **Pemisahan Wewenang Central Admin (`BD-001`):**
   * `is_central_admin` adalah atribut di dalam lingkup satu `tenant_id`. Central Admin hanya dapat mengelola master data (menu, varian, *add-on*, resep, harga, pajak, dan *service charge*) milik tenant-nya sendiri.
3. **Composite Foreign Keys di Level Database (`NFR-003`):**
   * Seluruh tabel transaksional dan master data memiliki kolom `tenant_id` dan menggunakan *composite foreign keys* `(tenant_id, id)`. Hal ini menjamin secara fisik di level PostgreSQL bahwa referensi lintas-tenant tidak pernah dapat terjadi.

---

# 4. Backend Modular Structure (FastAPI)

Struktur direktori backend dirancang modular agar setiap domain bisnis terisolasi dengan jelas (`NFR-019`, `NFR-020`):

```text
backend/
├── alembic/                    # Version-controlled database migrations (NFR-022)
├── app/
│   ├── core/
│   │   ├── config.py           # Environment variables & secrets (NFR-005, NFR-034)
│   │   ├── database.py         # Async/Sync SQLAlchemy session & transaction manager
│   │   ├── security.py         # Password hashing & JWT verification (NFR-002)
│   │   ├── permissions.py      # RBAC & Outlet-level authorization guards (NFR-004)
│   │   ├── exceptions.py       # Centralized error handling & uniform responses (NFR-024)
│   │   └── logging.py          # Structured JSON logging without sensitive data (NFR-025)
│   ├── modules/
│   │   ├── tenancy/            # Business registration, Outlets, Payment timing (FR-01)
│   │   ├── iam/                # Employees, Roles, Outlet assignments (FR-02, BD-001)
│   │   ├── catalog/            # Centralized Menu, Variants, Add-ons, Recipes, Availability (FR-03, BD-002)
│   │   ├── ordering/           # Tables, Single Active Order, Add Items, Modification Batch (FR-04, BD-004, BD-010)
│   │   ├── kitchen/            # Kitchen Queue, Submission Batches, Status Transitions (FR-05)
│   │   ├── pos/                # Checkout, Payments, Split Bill, Shifts, Void & Refunds (FR-06, FR-07, BD-005, BD-008, BD-009)
│   │   ├── inventory/          # Ingredients, On-Hand vs Reserved, Consumption on READY, Waste, Opname (FR-08, BD-003, BD-007)
│   │   ├── purchasing/         # Suppliers, Immutable Approved PO, Goods Receiving (FR-09, BD-006)
│   │   ├── reporting/          # Outlet & Consolidated Business Reports (FR-10, NFR-010)
│   │   └── audit/              # Immutable Activity & Change History (FR-11, NFR-007)
│   └── main.py                 # FastAPI app, /health & /ready endpoints (NFR-026), graceful shutdown (NFR-028)
└── tests/                      # Pytest suite covering business rules & isolation (NFR-023)
```

---

# 5. Data Integrity, Concurrency & Transaction Boundaries

Untuk memenuhi persyaratan keandalan transaksi dan pencegahan duplikasi (`NFR-012` hingga `NFR-015`):

1. **Atomic Database Transactions (`NFR-013`):**
   * **Submit Order ke Dapur:** Menyimpan `kitchen_submissions`, memperbarui `order_items`, mengecek stok tersedia, dan mencatat `inventory_reservations` dilakukan dalam satu transaksi atomik. Jika stok tidak mencukupi pada kebijakan *Strict Inventory*, seluruh transaksi di-*rollback*.
   * **Konfirmasi Item `READY` (`BD-003`):** Mengubah status `order_items.kitchen_status` menjadi `READY`, mengubah status `inventory_reservations` menjadi `CONSUMED`, memotong `inventory_balances.on_hand_qty` dan `reserved_qty`, serta mencatat `inventory_movements` dalam satu transaksi atomik.
   * **Goods Receiving (`BR-022`):** Menyimpan `goods_receipts`, memperbarui `purchase_order_items.received_qty`, memperbarui `inventory_balances.on_hand_qty`, menghitung ulang `average_unit_cost`, dan mencatat `inventory_movements` secara atomik.
2. **Idempotency Keys (`NFR-014`):**
   * Endpoint `POST /payments` mewajibkan `idempotency_key` unik per tenant untuk mencegah pemrosesan pembayaran ganda akibat *retry* jaringan.
3. **Optimistic Locking (`NFR-015`):**
   * Tabel `orders`, `inventory_balances`, dan `purchase_orders` dilengkapi kolom `version` (`INT`) untuk mendeteksi konflik modifikasi konkuren dan mencegah penimpaan data secara diam-diam.

---

# 6. Entity Relationship Diagram (ERD)

```text
[tenants] 1 ──────< [outlets]
   │                    │
   ├──< [users] ────────┼──< [user_outlet_roles] (RBAC per Outlet)
   │                    │
   ├──< [menu_categories]
   │       │
   └──< [products] ─────┼──< [outlet_product_availability]
           │            │
           ├──< [product_variants]
           ├──< [product_addons]
           └──< [recipe_items] ──> [ingredients]
                                      │
   ┌──────────────────────────────────┼──────────────────────────────────┐
   ▼                                  ▼                                  ▼
[inventory_balances]          [purchase_orders]                 [dining_tables]
(On-Hand & Reserved/Outlet)           │                                  │
   │                                  ├──< [purchase_order_items]        ▼
   ├──< [inventory_movements]         │           │                   [orders] (Single Active Order)
   │                                  └──< [goods_receipts]              │
   └──< [inventory_reservations]                  │                      ├──< [kitchen_submissions]
               ▲                                  └──< [goods_receipt_items]   │
               │                                                         ├──< [order_items] (Price Snapshot)
               └─────────────────────────────────────────────────────────┤
                                                                         ├──< [order_modification_requests]
                                                                         │
                                      [cashier_shifts] ──< [payments] ───┘
                                                              │
                                                              ├──< [payment_item_allocations]
                                                              └──< [refund_requests]
```

---

# 7. PostgreSQL Database Schema (DDL)

Skema berikut mengimplementasikan seluruh aturan bisnis (`BR-001` s.d. `BR-028`) dan klarifikasi (`BD-001` s.d. `BD-010`).

```sql
-- ============================================================================
-- EXTENSIONS & ENUMS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE payment_timing_enum AS ENUM ('PAY_BEFORE_SERVING', 'PAY_AFTER_SERVING');
CREATE TYPE order_type_enum AS ENUM ('DINE_IN', 'TAKEAWAY');
CREATE TYPE order_status_enum AS ENUM ('OPEN', 'CLOSED', 'CANCELLED');
CREATE TYPE payment_status_enum AS ENUM ('UNPAID', 'PARTIALLY_PAID', 'PAID', 'REFUNDED');
CREATE TYPE kitchen_status_enum AS ENUM ('PENDING', 'PREPARING', 'READY', 'SERVED', 'CANCELLED');
CREATE TYPE approval_status_enum AS ENUM ('PENDING', 'APPROVED', 'REJECTED');
CREATE TYPE po_status_enum AS ENUM (
    'DRAFT',
    'PENDING_APPROVAL',
    'APPROVED',
    'REJECTED',
    'PARTIALLY_RECEIVED',
    'COMPLETED',
    'CANCELLED'
);
CREATE TYPE movement_type_enum AS ENUM ('RECEIVING', 'CONSUMPTION', 'WASTE', 'ADJUSTMENT', 'OPNAME');
CREATE TYPE split_bill_type_enum AS ENUM ('NONE', 'SPLIT_BY_ITEMS', 'SPLIT_EQUALLY');

-- ============================================================================
-- 1. TENANCY, OUTLETS & IAM (FR-01, FR-02, BD-001)
-- ============================================================================
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    tax_rate NUMERIC(5,2) NOT NULL DEFAULT 0.00,             -- BR-006: Centralized Tax
    service_charge_rate NUMERIC(5,2) NOT NULL DEFAULT 0.00,  -- BR-006: Centralized Service Charge
    allow_negative_inventory BOOLEAN NOT NULL DEFAULT FALSE, -- BR-015, BR-016: Default Strict
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE outlets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    address TEXT,
    payment_timing payment_timing_enum NOT NULL DEFAULT 'PAY_AFTER_SERVING', -- BR-008
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, id)
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL,
    password_hash TEXT NOT NULL, -- NFR-002
    is_central_admin BOOLEAN NOT NULL DEFAULT FALSE, -- BD-001: Central Admin dalam lingkup Tenant
    is_owner BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, email),
    UNIQUE (tenant_id, id)
);

-- Penugasan peran operasional per outlet (FR-010, FR-011, FR-012)
-- Role values: 'MANAGER', 'CASHIER', 'WAITER', 'KITCHEN_STAFF', 'INVENTORY_STAFF', 'PURCHASING_STAFF'
CREATE TABLE user_outlet_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    user_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (tenant_id, user_id) REFERENCES users(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id) ON DELETE CASCADE,
    UNIQUE (tenant_id, user_id, outlet_id, role)
);

-- ============================================================================
-- 2. CENTRALIZED MENU & RECIPES (FR-03, BR-004, BR-005, BD-002)
-- ============================================================================
CREATE TABLE menu_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    name VARCHAR(100) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, id)
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    category_id UUID NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    base_price NUMERIC(12,2) NOT NULL CHECK (base_price >= 0), -- BR-005: Centralized Price
    allow_outlet_availability_override BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE, -- FR-023: Soft deactivate
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (tenant_id, category_id) REFERENCES menu_categories(tenant_id, id),
    UNIQUE (tenant_id, id)
);

CREATE TABLE product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    price_delta NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE,
    UNIQUE (tenant_id, id)
);

CREATE TABLE product_addons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    price NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (price >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE,
    UNIQUE (tenant_id, id)
);

-- Ketersediaan lokal per outlet tanpa mengubah definisi/harga pusat (FR-021)
CREATE TABLE outlet_product_availability (
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    product_id UUID NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, outlet_id, product_id),
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE
);

-- ============================================================================
-- 3. INGREDIENTS, RECIPES & INVENTORY (FR-08, BR-015 s.d. BR-020, BD-002, BD-003, BD-007)
-- ============================================================================
CREATE TABLE ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    unit VARCHAR(30) NOT NULL,
    min_stock_threshold NUMERIC(12,3) NOT NULL DEFAULT 0,
    average_unit_cost NUMERIC(12,2) NOT NULL DEFAULT 0, -- Untuk Basic Food Cost (FR-086)
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (tenant_id, id)
);

-- BD-002: Resep terpusat per produk (dan opsional per varian)
CREATE TABLE recipe_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    product_id UUID NOT NULL,
    variant_id UUID NULL,
    ingredient_id UUID NOT NULL,
    quantity_required NUMERIC(12,3) NOT NULL CHECK (quantity_required > 0),
    FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, variant_id) REFERENCES product_variants(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id) ON DELETE RESTRICT
);

-- Saldo stok independen per outlet (FR-065)
-- Available Stock dihitung = on_hand_qty - reserved_qty (BR-017, BR-018)
CREATE TABLE inventory_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    ingredient_id UUID NOT NULL,
    on_hand_qty NUMERIC(12,3) NOT NULL DEFAULT 0,
    reserved_qty NUMERIC(12,3) NOT NULL DEFAULT 0,
    version INT NOT NULL DEFAULT 1, -- Optimistic locking (NFR-015)
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id) ON DELETE RESTRICT,
    UNIQUE (tenant_id, outlet_id, ingredient_id)
);

-- Immutable ledger pergerakan stok (FR-072, BR-028)
CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    ingredient_id UUID NOT NULL,
    movement_type movement_type_enum NOT NULL,
    quantity_delta NUMERIC(12,3) NOT NULL,
    unit_cost NUMERIC(12,2),
    reference_type VARCHAR(50), -- 'ORDER_ITEM', 'GOODS_RECEIPT', 'MANUAL_ADJUSTMENT', 'STOCK_OPNAME'
    reference_id UUID,
    reason TEXT,
    is_negative_stock_exception BOOLEAN NOT NULL DEFAULT FALSE, -- BD-007
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
    FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id),
    FOREIGN KEY (tenant_id, created_by) REFERENCES users(tenant_id, id)
);

-- ============================================================================
-- 4. PURCHASING & GOODS RECEIVING (FR-09, BR-021, BR-022, BD-006)
-- ============================================================================
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    name VARCHAR(150) NOT NULL,
    contact_info TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (tenant_id, id)
);

CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    supplier_id UUID NOT NULL,
    po_number VARCHAR(50) NOT NULL,
    status po_status_enum NOT NULL DEFAULT 'DRAFT',
    requested_by UUID NOT NULL,
    approved_by UUID NULL, -- BR-021: Wajib Manager
    approved_at TIMESTAMPTZ NULL,
    rejection_reason TEXT NULL,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
    FOREIGN KEY (tenant_id, supplier_id) REFERENCES suppliers(tenant_id, id),
    FOREIGN KEY (tenant_id, requested_by) REFERENCES users(tenant_id, id),
    FOREIGN KEY (tenant_id, approved_by) REFERENCES users(tenant_id, id),
    UNIQUE (tenant_id, po_number),
    UNIQUE (tenant_id, id)
);

CREATE TABLE purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    purchase_order_id UUID NOT NULL,
    ingredient_id UUID NOT NULL,
    ordered_qty NUMERIC(12,3) NOT NULL CHECK (ordered_qty > 0),
    received_qty NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (received_qty >= 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    FOREIGN KEY (tenant_id, purchase_order_id) REFERENCES purchase_orders(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id),
    UNIQUE (tenant_id, id)
);

CREATE TABLE goods_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    purchase_order_id UUID NOT NULL,
    received_by UUID NOT NULL,
    notes TEXT,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
    FOREIGN KEY (tenant_id, purchase_order_id) REFERENCES purchase_orders(tenant_id, id),
    FOREIGN KEY (tenant_id, received_by) REFERENCES users(tenant_id, id),
    UNIQUE (tenant_id, id)
);

CREATE TABLE goods_receipt_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    goods_receipt_id UUID NOT NULL,
    po_item_id UUID NOT NULL,
    accepted_qty NUMERIC(12,3) NOT NULL CHECK (accepted_qty >= 0), -- BR-022: Hanya ini yang menambah stok
    rejected_qty NUMERIC(12,3) NOT NULL DEFAULT 0 CHECK (rejected_qty >= 0),
    FOREIGN KEY (tenant_id, goods_receipt_id) REFERENCES goods_receipts(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, po_item_id) REFERENCES purchase_order_items(tenant_id, id)
);

-- ============================================================================
-- 5. TABLES, ORDERS, KITCHEN & MODIFICATIONS (FR-04, FR-05, BR-009 s.d. BR-014, BD-004, BD-010)
-- ============================================================================
CREATE TABLE dining_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    table_number VARCHAR(30) NOT NULL,
    capacity INT NOT NULL DEFAULT 2,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
    UNIQUE (tenant_id, outlet_id, table_number),
    UNIQUE (tenant_id, id)
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    table_id UUID NULL, -- NULL jika TAKEAWAY
    order_number VARCHAR(50) NOT NULL,
    order_type order_type_enum NOT NULL,
    status order_status_enum NOT NULL DEFAULT 'OPEN', -- BD-004: CLOSED hanya jika PAID & semua item SERVED
    payment_status payment_status_enum NOT NULL DEFAULT 'UNPAID',
    -- Snapshot Tarif Pajak & Service Charge saat order dibuat (BR-007, FR-055)
    tax_rate_snapshot NUMERIC(5,2) NOT NULL,
    service_charge_rate_snapshot NUMERIC(5,2) NOT NULL,
    subtotal_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    tax_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    service_charge_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    grand_total_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_by UUID NOT NULL,
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ NULL,
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
    FOREIGN KEY (tenant_id, table_id) REFERENCES dining_tables(tenant_id, id),
    FOREIGN KEY (tenant_id, created_by) REFERENCES users(tenant_id, id),
    UNIQUE (tenant_id, order_number),
    UNIQUE (tenant_id, id)
);

-- BR-009: Menjamin secara fisik di level DB bahwa satu meja DINE_IN hanya punya 1 pesanan OPEN
CREATE UNIQUE INDEX uq_single_active_order_per_table 
ON orders (tenant_id, outlet_id, table_id) 
WHERE order_type = 'DINE_IN' AND status = 'OPEN';

-- BR-011: Setiap pengiriman item tambahan memiliki batch kitchen submission tersendiri
CREATE TABLE kitchen_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    order_id UUID NOT NULL,
    batch_number INT NOT NULL,
    submitted_by UUID NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, submitted_by) REFERENCES users(tenant_id, id),
    UNIQUE (tenant_id, id)
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    order_id UUID NOT NULL,
    kitchen_submission_id UUID NULL,
    product_id UUID NOT NULL,
    variant_id UUID NULL,
    -- Snapshot nama & harga saat transaksi dibuat (BR-007, FR-035)
    product_name_snapshot VARCHAR(150) NOT NULL,
    variant_name_snapshot VARCHAR(100) NULL,
    unit_price_snapshot NUMERIC(12,2) NOT NULL,
    addons_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
    quantity INT NOT NULL CHECK (quantity > 0),
    line_total NUMERIC(12,2) NOT NULL,
    special_instructions TEXT,
    kitchen_status kitchen_status_enum NOT NULL DEFAULT 'PENDING', -- FR-039
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, kitchen_submission_id) REFERENCES kitchen_submissions(tenant_id, id),
    FOREIGN KEY (tenant_id, product_id) REFERENCES products(tenant_id, id),
    UNIQUE (tenant_id, id)
);

-- Melacak reservasi stok per order_item sebelum item menjadi READY (BD-003, BD-007)
CREATE TABLE inventory_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    order_item_id UUID NOT NULL,
    ingredient_id UUID NOT NULL,
    reserved_qty NUMERIC(12,3) NOT NULL CHECK (reserved_qty > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'CONSUMED', 'RELEASED'
    is_negative_exception BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ NULL,
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
    FOREIGN KEY (tenant_id, order_item_id) REFERENCES order_items(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, ingredient_id) REFERENCES ingredients(tenant_id, id)
);

-- BR-012, BR-013, BD-010: Permintaan modifikasi/pembatalan saat item berstatus PREPARING
CREATE TABLE order_modification_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    order_id UUID NOT NULL,
    reason TEXT NOT NULL,
    status approval_status_enum NOT NULL DEFAULT 'PENDING',
    requested_by UUID NOT NULL,
    reviewed_by UUID NULL, -- Wajib Manager
    rejection_reason TEXT NULL,
    items_payload JSONB NOT NULL, -- Detail item dalam satu batch modifikasi (BD-010)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ NULL,
    FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id),
    FOREIGN KEY (tenant_id, requested_by) REFERENCES users(tenant_id, id),
    FOREIGN KEY (tenant_id, reviewed_by) REFERENCES users(tenant_id, id)
);

-- ============================================================================
-- 6. CASHIER SHIFTS, PAYMENTS, SPLIT BILL & REFUNDS (FR-06, FR-07, BR-023 s.d. BR-026, BD-008, BD-009)
-- ============================================================================
CREATE TABLE cashier_shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    cashier_id UUID NOT NULL,
    opening_cash NUMERIC(12,2) NOT NULL DEFAULT 0,
    expected_cash NUMERIC(12,2) NULL,
    actual_cash NUMERIC(12,2) NULL,
    cash_discrepancy NUMERIC(12,2) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'CLOSED'
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ NULL,
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
    FOREIGN KEY (tenant_id, cashier_id) REFERENCES users(tenant_id, id),
    UNIQUE (tenant_id, id)
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    order_id UUID NOT NULL,
    shift_id UUID NOT NULL,
    idempotency_key VARCHAR(100) NOT NULL, -- NFR-014: Cegah pembayaran ganda
    payment_method VARCHAR(50) NOT NULL, -- 'CASH', 'QRIS_MANUAL', 'CARD_MANUAL', 'TRANSFER_MANUAL'
    split_type split_bill_type_enum NOT NULL DEFAULT 'NONE',
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    processed_by UUID NOT NULL,
    paid_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
    FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id),
    FOREIGN KEY (tenant_id, shift_id) REFERENCES cashier_shifts(tenant_id, id),
    FOREIGN KEY (tenant_id, processed_by) REFERENCES users(tenant_id, id),
    UNIQUE (tenant_id, idempotency_key),
    UNIQUE (tenant_id, id)
);

-- Mencegah satu item dibayar dua kali pada mode SPLIT_BY_ITEMS (BRD 4.8.3)
CREATE TABLE payment_item_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    payment_id UUID NOT NULL,
    order_item_id UUID NOT NULL,
    allocated_qty INT NOT NULL CHECK (allocated_qty > 0),
    allocated_amount NUMERIC(12,2) NOT NULL,
    FOREIGN KEY (tenant_id, payment_id) REFERENCES payments(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, order_item_id) REFERENCES order_items(tenant_id, id)
);

-- BR-023, BR-024, BD-005, BD-009: Approval-based Refund
CREATE TABLE refund_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    outlet_id UUID NOT NULL,
    order_id UUID NOT NULL,
    payment_id UUID NOT NULL,
    refund_amount NUMERIC(12,2) NOT NULL CHECK (refund_amount > 0),
    reason TEXT NOT NULL,
    status approval_status_enum NOT NULL DEFAULT 'PENDING',
    requested_by UUID NOT NULL, -- Cashier
    reviewed_by UUID NULL,      -- Wajib Manager
    rejection_reason TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ NULL,
    FOREIGN KEY (tenant_id, outlet_id) REFERENCES outlets(tenant_id, id),
    FOREIGN KEY (tenant_id, order_id) REFERENCES orders(tenant_id, id),
    FOREIGN KEY (tenant_id, payment_id) REFERENCES payments(tenant_id, id),
    FOREIGN KEY (tenant_id, requested_by) REFERENCES users(tenant_id, id),
    FOREIGN KEY (tenant_id, reviewed_by) REFERENCES users(tenant_id, id)
);

-- ============================================================================
-- 7. IMMUTABLE AUDIT LOGS (FR-11, BR-027, NFR-007)
-- ============================================================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    outlet_id UUID NULL,
    actor_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    old_values JSONB NULL,
    new_values JSONB NULL,
    reason TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 8. STRATEGIC INDEXES FOR PERFORMANCE (NFR-008, NFR-011)
-- ============================================================================
CREATE INDEX idx_orders_tenant_outlet_status ON orders(tenant_id, outlet_id, status);
CREATE INDEX idx_order_items_kitchen ON order_items(tenant_id, kitchen_status);
CREATE INDEX idx_inventory_movements_lookup ON inventory_movements(tenant_id, outlet_id, ingredient_id, created_at DESC);
CREATE INDEX idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at DESC);
```

---

# 8. Requirements Traceability Matrix

Tabel berikut memetakan relasi langsung antara aturan bisnis, skema tabel database, dan modul backend:

| Business Rule / Clarification | Database Table / Constraint | Backend Module |
|---|---|---|
| `BR-001`, `NFR-003` (Tenant Isolation) | `tenants` & Composite FKs `(tenant_id, id)` di semua tabel | `core/permissions.py`, `tenancy` |
| `BR-004`, `BR-005`, `BD-001`, `BD-002` (Centralized Menu & Recipes) | `products`, `product_variants`, `product_addons`, `recipe_items` (level `tenant_id`) | `catalog` |
| `BR-007`, `FR-055` (Historical Snapshots) | `orders.*_snapshot`, `order_items.*_snapshot` | `ordering`, `pos` |
| `BR-008` (Per-Outlet Payment Timing) | `outlets.payment_timing` | `tenancy`, `pos` |
| `BR-009`, `BD-004` (Single Active Order & Dual Closure) | `uq_single_active_order_per_table` & `orders.status` | `ordering` |
| `BR-011` (Kitchen Submission Batches) | `kitchen_submissions` | `kitchen` |
| `BR-012`, `BR-013`, `BD-010` (Controlled Modification) | `order_modification_requests` (`items_payload` JSONB) | `ordering`, `kitchen` |
| `BR-015`–`BR-019`, `BD-003`, `BD-007` (Reservation & Consumption) | `inventory_balances`, `inventory_reservations`, `inventory_movements` | `inventory`, `kitchen` |
| `BR-021`, `BR-022`, `BD-006` (Approval-Based & Immutable PO) | `purchase_orders`, `goods_receipts`, `goods_receipt_items` | `purchasing`, `inventory` |
| `BR-023`–`BR-026`, `BD-005`, `BD-008`, `BD-009` (Payments, Split & Refunds) | `payments`, `payment_item_allocations`, `refund_requests` | `pos` |
| `BR-027`, `FR-11` (Audit Trail) | `audit_logs` | `audit` |

---

# 9. Document Status & Next Step

**Status:** Approved — Technical Architecture & Database Baseline Complete.  
**Next Step:** Penyusunan **Implementation Plan** dan inisialisasi struktur proyek (*scaffolding*) FastAPI + PostgreSQL + Docker + Next.js.
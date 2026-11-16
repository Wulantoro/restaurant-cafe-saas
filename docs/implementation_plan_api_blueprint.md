# Implementation Plan & API Blueprint
## Restaurant & Café Management System

**Document ID:** IMP-API-FOUNDATION-001  
**Version:** 1.0.0  
**Status:** Approved — Execution Roadmap  
**Related Documents:**
- `PRD-FOUNDATION-001` — Product Vision & Scope (v1.0.0)
- `BRD-FOUNDATION-001` — Business Requirements & Workflow (v2.0.0)
- `FRD-FOUNDATION-001` — Functional & Non-Functional Requirements (v1.0.0)
- `SAD-FOUNDATION-001` — System Architecture & Database Design (v1.0.0)
- `Document Revision Pack` — Business Clarifications (`BD-001` through `BD-010`)

---

# PART 1: API DESIGN STANDARDS & CONVENTIONS

Mengacu pada `SAD-FOUNDATION-001` dan `FRD Section 4 (NFR)`, seluruh *endpoint* REST API pada backend FastAPI wajib mematuhi standar berikut:

### 1.1 Base URL & Versioning
* Prefix standar: `/api/v1`
* Dokumentasi interaktif OpenAPI / Swagger UI tersedia di `/docs` (`NFR-021`).
* Endpoint operasional infrastruktur (`NFR-026`):
  * `GET /health` (Liveness check)
  * `GET /ready` (Readiness check, memverifikasi koneksi PostgreSQL)

### 1.2 Multi-Tenant & Outlet Context Isolation (`NFR-003`, `NFR-004`)
* `tenant_id` **tidak pernah** dikirim melalui *request body* untuk operasi operasional. `tenant_id` diekstrak secara eksklusif dari token JWT pengguna yang terautentikasi (`get_current_tenant_context`).
* Untuk sumber daya tingkat outlet, path menggunakan pola `/api/v1/outlets/{outlet_id}/...` dan backend memvalidasi bahwa pengguna memiliki peran aktif pada `outlet_id` tersebut (atau berstatus `is_owner` / `is_central_admin` sesuai cakupan izinnya).

### 1.3 Idempotency & Concurrency Control (`NFR-014`, `NFR-015`)
* **Idempotency Header:** Endpoint mutasi kritis (`POST .../payments`, `POST .../kitchen-submissions`, `POST .../goods-receipts`) mewajibkan header `Idempotency-Key: <uuid-v4>`. Jika kunci yang sama dikirim ulang dalam tenant yang sama, server mengembalikan hasil transaksi sebelumnya tanpa memproses ulang.
* **Optimistic Locking:** Request `PATCH`/`PUT` pada entitas dengan *versioning* (`orders`, `purchase_orders`, `inventory_balances`) wajib menyertakan field `version`. Jika terjadi konflik konkurensi, API mengembalikan status `409 Conflict`.

### 1.4 Uniform Response & Error Format (`NFR-024`)
* **Format Sukses:**
  ```json
  {
    "status": "success",
    "data": { ... },
    "meta": { "page": 1, "limit": 20, "total": 100 }
  }
  ```
* **Format Error Terpusat:**
  ```json
  {
    "status": "error",
    "error": {
      "code": "INSUFFICIENT_STOCK",
      "message": "Available stock for Arabica Beans is insufficient under Strict Inventory policy.",
      "details": { "ingredient_id": "...", "required": 50.0, "available": 20.0 }
    }
  }
  ```

---

# PART 2: CORE API ENDPOINT SPECIFICATION

Daftar *endpoint* inti berikut diturunkan langsung dari kebutuhan fungsional `FR-01` hingga `FR-11`:

### 2.1 Tenancy, Auth & IAM (`FR-01`, `FR-02`, `BD-001`)
* `POST /api/v1/auth/register-business` — Registrasi bisnis baru (membuat `tenant`, `owner` user, dan `outlet` pertama).
* `POST /api/v1/auth/login` — Autentikasi email & password, mengembalikan JWT Access & Refresh Token.
* `GET /api/v1/auth/me` — Profil pengguna aktif, status `is_owner`/`is_central_admin`, dan daftar outlet beserta perannya.
* `PATCH /api/v1/tenant/settings` — Konfigurasi terpusat `tax_rate`, `service_charge_rate` (Central Admin/Owner) dan `allow_negative_inventory` (khusus Owner/Manager berwenang, `BR-016`).
* `POST /api/v1/outlets` & `PATCH /api/v1/outlets/{outlet_id}` — Kelola outlet & pengaturan `payment_timing` (`PAY_BEFORE_SERVING` / `PAY_AFTER_SERVING`, `BR-008`).
* `POST /api/v1/users` & `POST /api/v1/users/{user_id}/roles` — Manajemen karyawan, status aktif, serta penugasan peran per outlet (`FR-010`–`FR-014`).

### 2.2 Centralized Menu, Recipes & Availability (`FR-03`, `BD-002`)
* `POST /api/v1/catalog/categories` & `GET /api/v1/catalog/categories` — Kelola kategori menu terpusat.
* `POST /api/v1/catalog/products` & `PATCH /api/v1/catalog/products/{product_id}` — Kelola produk, harga pusat (`BR-005`), varian, dan *add-on* (khusus Central Admin).
* `PUT /api/v1/catalog/products/{product_id}/recipe` — Kelola komposisi resep terpusat per produk/varian (`BD-002`).
* `PATCH /api/v1/outlets/{outlet_id}/products/{product_id}/availability` — Ubah ketersediaan lokal produk di outlet tertentu sesuai kebijakan pusat (`FR-021`).

### 2.3 Inventory & Purchasing (`FR-08`, `FR-09`, `BD-003`, `BD-006`, `BD-007`)
* `POST /api/v1/inventory/ingredients` & `GET /api/v1/outlets/{outlet_id}/inventory` — Master bahan baku pusat & pemantauan `on_hand_qty`, `reserved_qty`, serta `available_qty` per outlet.
* `POST /api/v1/outlets/{outlet_id}/inventory/adjustments` — Pencatatan *Waste*, *Manual Adjustment*, dan *Stock Opname* dengan alasan wajib (`BR-020`, `FR-070`, `FR-071`).
* `POST /api/v1/suppliers` — Manajemen data pemasok (*supplier*).
* `POST /api/v1/outlets/{outlet_id}/purchase-orders` — Pembuatan draf PO oleh *Purchasing Staff*.
* `POST /api/v1/outlets/{outlet_id}/purchase-orders/{po_id}/submit` — Ajukan PO untuk persetujuan Manager.
* `POST /api/v1/outlets/{outlet_id}/purchase-orders/{po_id}/review` — Persetujuan (`APPROVED`) atau penolakan (`REJECTED` + alasan wajib) oleh Manager (`BR-021`).
* `POST /api/v1/outlets/{outlet_id}/purchase-orders/{po_id}/cancel` — Pembatalan PO yang belum diterima jika perlu revisi (`BD-006`).
* `POST /api/v1/outlets/{outlet_id}/goods-receipts` — Konfirmasi penerimaan barang (mendukung *partial receiving* & penolakan barang rusak, `BR-022`, `FR-077`).

### 2.4 Tables, Orders & Kitchen Operations (`FR-04`, `FR-05`, `BD-004`, `BD-010`)
* `GET /api/v1/outlets/{outlet_id}/tables` & `POST /api/v1/outlets/{outlet_id}/tables` — Kelola meja dan lihat status okupansi (kosong / terisi pesanan `OPEN`).
* `POST /api/v1/outlets/{outlet_id}/orders` — Buat pesanan `DINE_IN` (gagal jika meja masih memiliki pesanan `OPEN`, `BR-009`) atau `TAKEAWAY`.
* `POST /api/v1/outlets/{outlet_id}/orders/{order_id}/items` — Tambah item ke pesanan aktif beserta varian, *add-on*, catatan khusus, dan penyimpanan *price snapshot* (`BR-010`, `FR-035`).
* `POST /api/v1/outlets/{outlet_id}/orders/{order_id}/submit-kitchen` — Kirim item baru ke dapur: membuat `kitchen_submissions` batch baru dan mengunci `inventory_reservations` (`BR-011`, `BR-017`).
* `GET /api/v1/outlets/{outlet_id}/kitchen/queue` — Antrean dapur per outlet dikelompokkan berdasarkan batch/pesanan.
* `PATCH /api/v1/outlets/{outlet_id}/kitchen/items/{item_id}/status` — Perbarui status item (`PREPARING`, `READY`, `SERVED`). Transisi ke `READY` otomatis memotong `on_hand_qty` sesuai resep (`BD-003`).
* `POST /api/v1/outlets/{outlet_id}/orders/{order_id}/void-pending` — Pembatalan item berstatus `PENDING` langsung oleh Waiter/Cashier (`BD-005`).
* `POST /api/v1/outlets/{outlet_id}/orders/{order_id}/modification-requests` — Pengajuan batch modifikasi/pembatalan item berstatus `PREPARING` (`BD-010`).
* `POST /api/v1/outlets/{outlet_id}/modification-requests/{req_id}/review` — Persetujuan/penolakan batch modifikasi oleh Manager (`BR-013`).

### 2.5 Cashier Shifts, POS Payments & Refunds (`FR-06`, `FR-07`, `BD-005`, `BD-008`, `BD-009`)
* `POST /api/v1/outlets/{outlet_id}/shifts/open` & `POST /api/v1/outlets/{outlet_id}/shifts/{shift_id}/close` — Buka dan tutup shift kasir dengan rekonsiliasi kas aktual vs ekspektasi (`FR-056`–`FR-062`).
* `POST /api/v1/outlets/{outlet_id}/orders/{order_id}/payments` — Proses pembayaran penuh, parsial, maupun *Split Bill* (`SPLIT_BY_ITEMS` / `SPLIT_EQUALLY`) dengan validasi kebijakan `payment_timing` outlet (`BD-008`).
* `GET /api/v1/outlets/{outlet_id}/orders/{order_id}/receipt` — Cetak/tampilkan struk transaksi berdasarkan *snapshot* historis (`FR-052`, `FR-055`).
* `POST /api/v1/outlets/{outlet_id}/payments/{payment_id}/refund-requests` — Pengajuan *refund* oleh Kasir (`BR-024`, `BD-009`).
* `POST /api/v1/outlets/{outlet_id}/refund-requests/{req_id}/review` — Persetujuan/penolakan *refund* oleh Manager (`BR-023`).

### 2.6 Reports & Audit Trail (`FR-10`, `FR-11`)
* `GET /api/v1/reports/daily-sales` — Laporan penjualan harian (filter per outlet atau gabungan seluruh bisnis, `FR-080`, `FR-088`, `FR-089`).
* `GET /api/v1/reports/best-selling` — Laporan menu terlaris (`FR-083`).
* `GET /api/v1/reports/inventory-summary` — Laporan posisi stok, stok minimum, dan *basic food cost* (`FR-084`, `FR-086`).
* `GET /api/v1/audit-logs` — Riwayat audit aktivitas sensitif dengan filter entitas, aktor, dan tanggal (`FR-091`–`FR-095`).

---

# PART 3: PHASED IMPLEMENTATION PLAN (MVP ROADMAP)

Pengembangan dibagi ke dalam **7 Fase Terstruktur (Phase 0 – Phase 6)**. Setiap fase harus memenuhi *Definition of Done (DoD)* dan lulus uji otomatis Pytest sebelum berpindah ke fase berikutnya (`PRD Section 12`, `NFR-023`).

### Phase 0: Project Scaffolding, Docker & Database Foundation
* **Tujuan:** Menyiapkan fondasi repositori, lingkungan kontainer, dan skema PostgreSQL.
* **Deliverables:**
  1. Struktur folder monorepo (`backend/` untuk FastAPI, `frontend/` untuk Next.js).
  2. Konfigurasi `docker-compose.yml` (PostgreSQL 15, FastAPI Backend, Next.js Frontend).
  3. Setup `app/core/` (Config, Database session, Centralized Exception Handler, Structured JSON Logging, `/health` & `/ready` endpoints).
  4. Implementasi model SQLAlchemy dan migrasi awal Alembic sesuai DDL pada `SAD-FOUNDATION-001`.
* **Definition of Done (DoD):** Container berjalan lancar melalui Docker, migrasi Alembic sukses membuat seluruh tabel & *constraints*, serta `GET /ready` mengembalikan status `200 OK`.

### Phase 1: Multi-Tenant Auth, IAM & Outlet Configuration
* **Tujuan:** Mengamankan isolasi data antar-tenant dan penegakan hak akses berbasis peran & outlet.
* **Deliverables:**
  1. Modul `tenancy` & `iam`: Registrasi bisnis, login JWT, manajemen outlet (termasuk pengaturan `payment_timing`), serta penugasan peran karyawan per outlet dan flag `is_central_admin` / `is_owner`.
  2. Middleware/Dependency `get_current_tenant_context` dan *RBAC Permission Guards*.
* **Definition of Done (DoD):** Pengujian Pytest membuktikan pengguna Tenant A tidak dapat membaca/mengubah data Tenant B (`NFR-003`), dan staf Outlet 1 tidak dapat mengakses sumber daya Outlet 2 tanpa izin.

### Phase 2: Centralized Menu, Recipes & Outlet Availability
* **Tujuan:** Menyediakan manajemen katalog terpusat dan definisi resep standar.
* **Deliverables:**
  1. Modul `catalog`: CRUD Kategori, Produk, Varian, Add-on, serta Pengaturan Pajak & Service Charge terpusat (hanya dapat diakses `Central Admin` / `Owner`).
  2. Manajemen resep terpusat (`recipe_items`) yang menghubungkan produk/varian dengan bahan baku (`BD-002`).
  3. Toggle ketersediaan produk lokal per outlet (`outlet_product_availability`).
* **Definition of Done (DoD):** Staf outlet ditolak saat mencoba mengubah harga produk pusat (`BR-005`), namun dapat menandai produk *out-of-stock* di outletnya sendiri (`FR-021`).

### Phase 3: Inventory Engine & Approval-Based Purchasing
* **Tujuan:** Membangun mesin pelacakan stok (*On-Hand* vs *Reserved*) dan alur pengadaan barang.
* **Deliverables:**
  1. Modul `inventory`: Master bahan baku, *Manual Adjustment*, *Waste*, dan *Stock Opname* beserta pencatatan *ledger* `inventory_movements`.
  2. Modul `purchasing`: Pembuatan PO oleh *Purchasing Staff*, alur *Approval/Rejection* oleh *Manager*, kunci imutabilitas PO yang sudah disetujui (`BD-006`), dan *Goods Receiving* parsial (`BR-022`).
* **Definition of Done (DoD):** PO tidak dapat dikirim sebelum disetujui Manager, stok hanya bertambah setelah *Goods Receiving* dikonfirmasi, dan riwayat pergerakan stok tercatat lengkap.

### Phase 4: Table Management, Ordering & Kitchen Workflow
* **Tujuan:** Menghubungkan pemesanan meja dengan antrean dapur dan reservasi bahan baku otomatis.
* **Deliverables:**
  1. Modul `ordering`: Manajemen meja, *Single Active Order* per meja (`BR-009`), penambahan item dengan *price/tax snapshot* (`BR-007`), serta *Controlled Modification* (batch approval oleh Manager untuk status `PREPARING`, `BD-010`).
  2. Modul `kitchen`: Antrean dapur per batch (`kitchen_submissions`), pembaruan status (`PENDING` → `PREPARING` → `READY` → `SERVED`), reservasi stok saat *submit* ke dapur, dan pemotongan stok fisik otomatis saat `READY` (`BD-003`), termasuk penanganan kebijakan *Strict* vs *Allow Negative Inventory* (`BD-007`).
* **Definition of Done (DoD):** Pengujian Pytest memverifikasi siklus hidup reservasi stok (reservasi saat *submit*, rilis saat *void*, konsumsi saat `READY`), penolakan pesanan ke-2 pada meja yang masih `OPEN`, dan penutupan pesanan hanya saat `PAID` + semua item `SERVED` (`BD-004`).

### Phase 5: Cashier Shifts, POS Payments, Split Bill & Refunds
* **Tujuan:** Menyelesaikan siklus finansial transaksi pelanggan secara akurat dan aman dari duplikasi.
* **Deliverables:**
  1. Modul `pos`: Buka/tutup shift kasir dan perhitungan selisih kas (`FR-07`).
  2. Pemrosesan pembayaran tunai & non-tunai manual dengan validasi `Idempotency-Key` (`NFR-014`) dan kebijakan `Pay Before/After Serving` (`BR-008`).
  3. Kalkulasi *Split Bill* (`SPLIT_BY_ITEMS` dan `SPLIT_EQUALLY`) beserta alokasi pembulatan (`BD-008`).
  4. Alur pengajuan *Refund* oleh Kasir dan persetujuan *Manager* dengan batas maksimal dana bersih yang sudah dibayar (`BD-005`, `BD-009`).
* **Definition of Done (DoD):** Pengujian Pytest membuktikan pencegahan *double payment*, rekonsiliasi sen/rupiah yang tepat pada *split bill*, dan penolakan *refund* yang melebihi batas bayar.

### Phase 6: Reporting, Audit Trail & Frontend Web/Tablet UI
* **Tujuan:** Menyajikan visibilitas laporan bisnis, jejak audit lengkap, dan antarmuka pengguna Next.js.
* **Deliverables:**
  1. Modul `reporting` & `audit`: Laporan penjualan harian, menu terlaris, stok minimum, *basic food cost*, dan penelusuran *audit trail* untuk seluruh aksi sensitif (`FR-10`, `FR-11`).
  2. Aplikasi Frontend **Next.js + TypeScript** yang responsif untuk Desktop (Admin, Owner, Manager, Inventory, Purchasing) dan Tablet (Waiter, Cashier, Kitchen Display) (`NFR-031`).
  3. Konfigurasi CI/CD **GitHub Actions** untuk otomatisasi *Pytest* dan *build check* (`NFR-033`).
* **Definition of Done (DoD):** Seluruh 46 kriteria pada *Acceptance Criteria* (`Document Revision Pack Part E`) terverifikasi lulus dan siap untuk *deployment* MVP.
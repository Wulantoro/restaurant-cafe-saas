# Functional & Non-Functional Requirements
## Restaurant & Café Management System

**Document ID:** FRD-FOUNDATION-001  
**Version:** 1.0.0  
**Status:** Draft — Requirements Definition  
**Related Documents:**
- PRD-FOUNDATION-001 — Product Vision & Scope
- BRD-FOUNDATION-001 — Business Requirements & Workflow

---

# 1. Purpose

Dokumen ini mendefinisikan kebutuhan fungsional dan non-fungsional Restaurant & Café Management System.

Dokumen digunakan sebagai acuan untuk:
- System architecture.
- Database design.
- API specification.
- UI/UX design.
- Software implementation.
- Functional testing.
- Integration testing.
- Acceptance testing.

# 2. Requirement Priority

Setiap requirement memiliki prioritas:

| Priority | Meaning |
|---|---|
| MUST | Wajib tersedia untuk MVP |
| SHOULD | Sangat dianjurkan, tetapi dapat ditunda |
| COULD | Fitur tambahan jika waktu memungkinkan |

# 3. Functional Requirements

## FR-01 Business & Tenant Management

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Sistem harus memungkinkan pengguna mendaftarkan bisnis baru. | MUST |
| FR-002 | Sistem harus membuat tenant baru untuk setiap bisnis yang terdaftar. | MUST |
| FR-003 | Sistem harus memungkinkan pemilik memperbarui profil bisnis. | MUST |
| FR-004 | Sistem harus mendukung satu tenant dengan beberapa outlet. | MUST |
| FR-005 | Sistem harus memungkinkan pemilik membuat, mengubah, dan menonaktifkan outlet. | MUST |
| FR-006 | Sistem harus memungkinkan konfigurasi informasi dan operasional outlet. | MUST |
| FR-007 | Sistem harus menyediakan laporan gabungan untuk seluruh outlet dalam satu tenant. | MUST |

## FR-02 Authentication & Access Control

| ID | Requirement | Priority |
|---|---|---|
| FR-008 | Sistem harus menyediakan autentikasi pengguna. | MUST |
| FR-009 | Sistem harus mendukung logout dan pengelolaan sesi. | MUST |
| FR-010 | Sistem harus mendukung role-based access control (RBAC). | MUST |
| FR-011 | Sistem harus memungkinkan satu karyawan memiliki beberapa peran. | MUST |
| FR-012 | Sistem harus membatasi akses pengguna berdasarkan outlet. | MUST |
| FR-013 | Sistem harus menyediakan pengelolaan karyawan. | MUST |
| FR-014 | Sistem harus mendukung aktivasi dan penonaktifan akun karyawan. | MUST |
| FR-015 | Sistem harus memverifikasi izin sebelum menjalankan operasi yang dilindungi. | MUST |

## FR-03 Menu & Product Management

| ID | Requirement | Priority |
|---|---|---|
| FR-016 | Sistem harus menyediakan pengelolaan kategori menu. | MUST |
| FR-017 | Sistem harus menyediakan pengelolaan produk makanan dan minuman. | MUST |
| FR-018 | Sistem harus mendukung varian produk. | MUST |
| FR-019 | Sistem harus mendukung add-on dan modifier. | MUST |
| FR-020 | Sistem harus mendukung konfigurasi harga produk. | MUST |
| FR-021 | Sistem harus mendukung ketersediaan produk berdasarkan outlet. | MUST |
| FR-022 | Sistem harus mendukung konfigurasi resep produk. | MUST |
| FR-023 | Sistem harus memungkinkan produk dinonaktifkan tanpa menghapus riwayat transaksi. | MUST |

## FR-04 Table & Order Management

| ID | Requirement | Priority |
|---|---|---|
| FR-024 | Sistem harus menyediakan pengelolaan meja berdasarkan outlet. | MUST |
| FR-025 | Sistem harus menampilkan status ketersediaan meja. | MUST |
| FR-026 | Sistem harus mendukung pesanan dine-in. | MUST |
| FR-027 | Sistem harus mendukung pesanan takeaway. | MUST |
| FR-028 | Sistem harus memungkinkan pengguna menambahkan produk ke pesanan. | MUST |
| FR-029 | Sistem harus mendukung pemilihan varian dan add-on. | MUST |
| FR-030 | Sistem harus mendukung catatan khusus pada item pesanan. | MUST |
| FR-031 | Sistem harus menghitung subtotal pesanan secara otomatis. | MUST |
| FR-032 | Sistem harus mendukung penambahan item pada pesanan yang masih aktif. | MUST |
| FR-033 | Sistem harus menyediakan mekanisme pembatalan pesanan dengan otorisasi yang sesuai. | MUST |
| FR-034 | Sistem harus mencatat riwayat perubahan pesanan. | MUST |
| FR-035 | Sistem harus mempertahankan harga dan deskripsi item pada saat transaksi dibuat. | MUST |

## FR-05 Kitchen Operations

| ID | Requirement | Priority |
|---|---|---|
| FR-036 | Sistem harus mengirim item pesanan ke kitchen queue. | MUST |
| FR-037 | Sistem harus menampilkan antrean pesanan berdasarkan outlet. | MUST |
| FR-038 | Sistem harus menampilkan informasi item, jumlah, dan catatan khusus. | MUST |
| FR-039 | Sistem harus mendukung status PENDING, PREPARING, READY, SERVED, dan CANCELLED. | MUST |
| FR-040 | Sistem harus memungkinkan kitchen memperbarui status setiap item. | MUST |
| FR-041 | Sistem harus mendukung status penyelesaian parsial ketika item dalam satu pesanan selesai pada waktu berbeda. | MUST |
| FR-042 | Sistem harus mencatat waktu perubahan status kitchen. | SHOULD |

## FR-06 Point of Sale & Payment

| ID | Requirement | Priority |
|---|---|---|
| FR-043 | Sistem harus menyediakan tampilan transaksi kasir. | MUST |
| FR-044 | Sistem harus menghitung total tagihan secara otomatis. | MUST |
| FR-045 | Sistem harus mendukung konfigurasi pajak dan service charge. | MUST |
| FR-046 | Sistem harus mendukung diskon dengan otorisasi yang sesuai. | MUST |
| FR-047 | Sistem harus mendukung pembayaran tunai. | MUST |
| FR-048 | Sistem harus mendukung pencatatan pembayaran non-tunai secara manual. | MUST |
| FR-049 | Sistem harus mendukung split payment. | MUST |
| FR-050 | Sistem harus mencatat metode, nominal, dan waktu pembayaran. | MUST |
| FR-051 | Sistem harus mendukung status pembayaran UNPAID, PARTIALLY_PAID, PAID, dan REFUNDED. | MUST |
| FR-052 | Sistem harus menyediakan receipt transaksi. | MUST |
| FR-053 | Sistem harus mendukung refund dan void dengan otorisasi khusus. | MUST |
| FR-054 | Sistem harus mencegah pembayaran ganda atas tagihan yang sama. | MUST |
| FR-055 | Sistem harus menyimpan snapshot harga, diskon, pajak, dan service charge pada transaksi. | MUST |

## FR-07 Cashier Shift Management

| ID | Requirement | Priority |
|---|---|---|
| FR-056 | Sistem harus memungkinkan kasir membuka shift. | MUST |
| FR-057 | Sistem harus mencatat saldo awal kas. | MUST |
| FR-058 | Sistem harus menghubungkan transaksi kasir dengan shift aktif. | MUST |
| FR-059 | Sistem harus memungkinkan kasir menutup shift. | MUST |
| FR-060 | Sistem harus menghitung saldo kas berdasarkan transaksi tercatat. | MUST |
| FR-061 | Sistem harus mencatat saldo aktual dan selisih kas. | MUST |
| FR-062 | Sistem harus menyediakan laporan penutupan shift. | MUST |

## FR-08 Inventory Management

| ID | Requirement | Priority |
|---|---|---|
| FR-063 | Sistem harus menyediakan pengelolaan bahan baku. | MUST |
| FR-064 | Sistem harus mendukung satuan pengukuran bahan baku. | MUST |
| FR-065 | Sistem harus menyimpan stok berdasarkan outlet. | MUST |
| FR-066 | Sistem harus mencatat penerimaan stok. | MUST |
| FR-067 | Sistem harus mencatat pengurangan stok berdasarkan resep dan transaksi penjualan yang memenuhi aturan bisnis. | MUST |
| FR-068 | Sistem harus mencatat stock adjustment. | MUST |
| FR-069 | Sistem harus mendukung pencatatan waste. | MUST |
| FR-070 | Sistem harus mendukung stock opname. | MUST |
| FR-071 | Sistem harus menyediakan riwayat pergerakan stok. | MUST |
| FR-072 | Sistem harus menyediakan informasi stok minimum. | SHOULD |

## FR-09 Purchasing Management

| ID | Requirement | Priority |
|---|---|---|
| FR-073 | Sistem harus menyediakan pengelolaan pemasok. | MUST |
| FR-074 | Sistem harus memungkinkan pembuatan purchase order. | MUST |
| FR-075 | Sistem harus mendukung persetujuan purchase order. | MUST |
| FR-076 | Sistem harus mencatat barang yang diterima. | MUST |
| FR-077 | Sistem harus mendukung penerimaan barang sebagian. | MUST |
| FR-078 | Sistem harus memperbarui stok berdasarkan jumlah barang yang benar-benar diterima. | MUST |
| FR-079 | Sistem harus menyediakan riwayat purchase order. | MUST |

## FR-10 Reports & Analytics

| ID | Requirement | Priority |
|---|---|---|
| FR-080 | Sistem harus menyediakan laporan penjualan harian. | MUST |
| FR-081 | Sistem harus menyediakan laporan pesanan. | MUST |
| FR-082 | Sistem harus menyediakan laporan pembayaran. | MUST |
| FR-083 | Sistem harus menyediakan laporan menu terlaris. | MUST |
| FR-084 | Sistem harus menyediakan laporan stok. | MUST |
| FR-085 | Sistem harus menyediakan laporan pergerakan stok. | MUST |
| FR-086 | Sistem harus menyediakan laporan basic food cost. | MUST |
| FR-087 | Sistem harus mendukung filter laporan berdasarkan periode. | MUST |
| FR-088 | Sistem harus mendukung laporan per outlet. | MUST |
| FR-089 | Sistem harus mendukung laporan gabungan tingkat bisnis. | MUST |
| FR-090 | Sistem harus membatasi isi laporan sesuai hak akses pengguna. | MUST |

## FR-11 Audit & Activity History

| ID | Requirement | Priority |
|---|---|---|
| FR-091 | Sistem harus mencatat aktivitas penting pengguna. | MUST |
| FR-092 | Sistem harus mencatat perubahan data penting. | MUST |
| FR-093 | Sistem harus mencatat aktor, waktu, dan jenis perubahan. | MUST |
| FR-094 | Sistem harus mencatat alasan untuk operasi sensitif seperti refund, void, dan stock adjustment. | MUST |
| FR-095 | Sistem harus menyediakan akses riwayat aktivitas bagi pengguna yang berwenang. | SHOULD |

---

# 4. Non-Functional Requirements

## NFR-01 Security

| ID | Requirement |
|---|---|
| NFR-001 | Seluruh komunikasi aplikasi dengan backend harus menggunakan HTTPS pada deployment production. |
| NFR-002 | Password harus disimpan menggunakan password hashing yang aman. |
| NFR-003 | Sistem harus menerapkan tenant isolation pada seluruh akses data bisnis. |
| NFR-004 | Sistem harus memverifikasi otorisasi pada sisi backend, bukan hanya frontend. |
| NFR-005 | Secret dan credential tidak boleh disimpan dalam source code. |
| NFR-006 | Input pengguna harus divalidasi sebelum diproses. |
| NFR-007 | Operasi sensitif harus memiliki audit trail. |

## NFR-02 Performance

| ID | Requirement |
|---|---|
| NFR-008 | API operasional umum menargetkan response time P95 di bawah 500 ms pada kondisi beban yang ditentukan. |
| NFR-009 | Sistem harus mendukung pagination untuk daftar data berukuran besar. |
| NFR-010 | Query laporan harus dirancang agar tidak menghambat transaksi operasional. |
| NFR-011 | Sistem harus menghindari query database yang tidak efisien. |

## NFR-03 Reliability & Data Integrity

| ID | Requirement |
|---|---|
| NFR-012 | Operasi transaksi keuangan harus menjaga konsistensi data. |
| NFR-013 | Perubahan pesanan, pembayaran, dan stok yang saling bergantung harus menggunakan mekanisme transaksi database yang sesuai. |
| NFR-014 | Sistem harus mencegah pemrosesan ganda akibat request berulang pada operasi kritis. |
| NFR-015 | Sistem harus menangani konflik perubahan data secara konsisten. |
| NFR-016 | Sistem harus menyediakan mekanisme backup dan pemulihan database. |

## NFR-04 Scalability

| ID | Requirement |
|---|---|
| NFR-017 | Sistem harus mendukung pertumbuhan jumlah tenant dan outlet. |
| NFR-018 | Sistem harus mendukung peningkatan jumlah pengguna dan transaksi. |
| NFR-019 | Komponen aplikasi harus dirancang agar dapat dikembangkan dan diskalakan tanpa mengubah keseluruhan sistem. |

## NFR-05 Maintainability

| ID | Requirement |
|---|---|
| NFR-020 | Source code harus menggunakan struktur modular dan konsisten. |
| NFR-021 | Sistem harus menyediakan dokumentasi API. |
| NFR-022 | Perubahan database harus dikelola menggunakan migration. |
| NFR-023 | Sistem harus memiliki automated tests. |
| NFR-024 | Sistem harus menggunakan centralized error handling. |
| NFR-025 | Sistem harus menyediakan structured logging. |

## NFR-06 Availability & Observability

| ID | Requirement |
|---|---|
| NFR-026 | Sistem harus menyediakan health check endpoint. |
| NFR-027 | Sistem harus mencatat error dan kegagalan operasi penting. |
| NFR-028 | Sistem harus mendukung graceful shutdown. |
| NFR-029 | Sistem harus menyediakan informasi yang cukup untuk memantau kondisi aplikasi. |

## NFR-07 Compatibility & Deployment

| ID | Requirement |
|---|---|
| NFR-030 | Web application harus mendukung browser modern. |
| NFR-031 | Web interface harus responsif untuk desktop dan tablet. |
| NFR-032 | Deployment harus mendukung Docker. |
| NFR-033 | CI/CD harus mendukung automated testing dan build verification melalui GitHub Actions. |
| NFR-034 | Sistem harus mendukung pengembangan dan deployment environment yang terpisah. |

---

# 5. Acceptance Criteria

MVP dianggap memenuhi kebutuhan dasar apabila:

1. Pengguna dapat membuat tenant dan mengelola beberapa outlet.
2. Pengguna dapat mengelola karyawan serta hak aksesnya.
3. Setiap outlet dapat mengelola menu dan resep.
4. Pengguna dapat membuat pesanan dine-in dan takeaway.
5. Pesanan dapat diteruskan ke kitchen dan statusnya diperbarui.
6. Kasir dapat menyelesaikan pembayaran.
7. Sistem dapat mencatat shift kasir.
8. Sistem dapat memperbarui stok berdasarkan aktivitas operasional.
9. Pengguna dapat mengelola pembelian dan penerimaan stok.
10. Pemilik dapat melihat laporan outlet dan laporan gabungan.
11. Data tenant terisolasi dan akses outlet dibatasi.
12. Automated tests memverifikasi alur utama dan kondisi kegagalan penting.

# 6. Requirements Traceability

Setiap requirement harus dapat ditelusuri ke:
- Business workflow yang menjadi sumber kebutuhan.
- Modul aplikasi yang mengimplementasikan kebutuhan.
- API atau UI yang berkaitan.
- Test case yang memverifikasi hasilnya.

Format ID requirement harus dipertahankan selama proses desain dan implementasi agar perubahan dapat dilacak.

# 7. Open Decisions

Requirement berikut masih memerlukan keputusan bisnis sebelum desain teknis final:

1. Pembayaran sebelum atau sesudah penyajian.
2. Kebijakan stok negatif.
3. Perubahan pesanan setelah dikirim ke kitchen.
4. Beberapa pesanan aktif pada satu meja.
5. Pengelolaan harga terpusat atau per outlet.
6. Persetujuan purchase order.
7. Persetujuan refund.
8. Konfigurasi pajak dan service charge per outlet.
9. Split bill berdasarkan item atau pelanggan.
10. Aturan pengurangan stok ketika pesanan dibatalkan.

Requirement yang dipengaruhi keputusan tersebut harus dikonfirmasi sebelum masuk implementasi.

# 8. Status

**Current status:** Draft — Requirements Definition.

Functional scope sudah diturunkan dari Product Vision & Scope dan Business Requirements & Workflow.

Prioritas dan acceptance criteria awal sudah didefinisikan. Beberapa business rules masih menunggu konfirmasi.

**Next document:** System Architecture Document (SAD).
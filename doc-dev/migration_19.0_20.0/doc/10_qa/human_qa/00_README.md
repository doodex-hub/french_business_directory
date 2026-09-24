# Human QA Checklists — french_business_directory (Odoo 20.0)

**Sumber:** skenario S-01..S-10 di `../10_BUSINESS_FLOW_MIGRATION.md`, dikelompokkan per Level. Kalau skenario/level di file itu berubah, regenerate file di folder ini juga.

Dibuat di Step 10 walaupun skenario dijalankan AI (Playwright MCP) — supaya dev/QA/PM bisa re-verifikasi sendiri tanpa AI.

| File | Isi | Kapan dipakai |
|---|---|---|
| `01_SMOKE.md` | Tombol & wizard terbuka | Sebelum deploy/hotfix |
| `02_MAIN_FLOW.md` | Company tanpa VAT, paginasi, Select | QA rutin |
| `03_DETAIL.md` | Tampilan hasil, field Mark as Read | Sebelum rilis besar |
| `04_NEGATIVE.md` | Select setelah paginasi (bug bawaan RMV-02), field tersembunyi | Minimal sekali sebelum rilis besar |

**Catatan environment:** API `recherche-entreprises.api.gouv.fr` kadang membalas 429 (terlalu banyak request) → muncul dialog "Oops" (bug bawaan RMV-03). Tunggu ±10 detik lalu ulangi — itu bukan kegagalan checklist.

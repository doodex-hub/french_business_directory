# Human QA Checklists — french_business_directory (Odoo 20.0)

**Sumber:** skenario S-01..S-10 di `../10_BUSINESS_FLOW_MIGRATION.md`, dikelompokkan per Level. Kalau skenario/level di file itu berubah, regenerate file di folder ini juga.

Dibuat di Step 10 walaupun skenario dijalankan AI (Playwright MCP) — supaya dev/QA/PM bisa re-verifikasi sendiri tanpa AI.

| File | Isi | Kapan dipakai |
|---|---|---|
| `01_SMOKE.md` | Tombol & wizard terbuka | Sebelum deploy/hotfix |
| `02_MAIN_FLOW.md` | Company tanpa VAT, paginasi, Select | QA rutin |
| `03_DETAIL.md` | Tampilan hasil, field Mark as Read | Sebelum rilis besar |
| `04_NEGATIVE.md` | Select setelah paginasi (bug bawaan RMV-02), field tersembunyi | Minimal sekali sebelum rilis besar |

**Catatan environment:** API `recherche-entreprises.api.gouv.fr` (gratis, dibatasi 7 panggilan/detik) kadang membalas 429. Sejak perbaikan RMV-03 modul menunggu & mencoba ulang otomatis; kalau tetap sibuk muncul pesan Inggris "The company directory service … is busy right now …" — tunggu sebentar lalu ulangi. Itu bukan kegagalan checklist. Dialog "Oops" dengan traceback TIDAK boleh muncul lagi (kecuali RMV-05, nama perusahaan tertentu).

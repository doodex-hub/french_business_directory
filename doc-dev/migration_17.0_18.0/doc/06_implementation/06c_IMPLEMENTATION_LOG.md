# Implementation Log — french_business_directory

**Step:** 6 — Code Migration
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `06a_CODE_MIGRATION_PHASES.md`
**Tanggal:** 2026-08-24

---

## Applicability Check

| Fase | Relevan? | Bukti/alasan (dari `01a` §2b) |
|---|---|---|
| B2 — Model Kompleks | ☐ Tidak | Tidak ada field JSON, relasi >2 level, atau dynamic model creation di kedua addon |
| C2 — Semantik XML & UX | ☐ Tidak | Tidak ada `attrs`/`states`/`domain`/`context` dinamis di view manapun |
| D1 — Controllers | ☐ Tidak | Tidak ada folder `controllers/` di kedua addon |
| D2 — Assets & CSS | ☐ Tidak | Tidak ada asset custom (`assets: {}` kosong, tidak ada `static/src/`) |
| E — JavaScript (Owl) | ☐ Tidak | Tidak ada file `.js` di kedua addon |
| F — Upgrade Template | ☐ Tidak | Otomatis N/A karena E N/A |

## Tabel Ringkas Status Fase

| Fase | Status | Tanggal |
|---|---|---|
| A1 | ✅ | 2026-08-24 |
| A2 | ✅ | 2026-08-24 |
| G1 (checkpoint #1, setelah A2) | 🔄 Sedang berjalan (background) | 2026-08-24 |
| A3 | ✅ (tidak ada perubahan diperlukan) | 2026-08-24 |
| A4 | ✅ (tidak ada perubahan diperlukan) | 2026-08-24 |
| A5 | ✅ (termasuk addendum DIFF-09) | 2026-08-24 |
| B1 | ✅ | 2026-08-24 |
| B2 | N/A — dikonfirmasi Applicability Check | |
| C1 | ✅ | 2026-08-24 |
| C2 | N/A — dikonfirmasi Applicability Check | |
| D1 | N/A — dikonfirmasi Applicability Check | |
| D2 | N/A — dikonfirmasi Applicability Check | |
| E | N/A — dikonfirmasi Applicability Check | |
| F | N/A — dikonfirmasi Applicability Check | |
| G2 (validasi akhir/runtime) | ✅ | 2026-08-24 |

## Riwayat Percobaan G1 (Install Test)

> **Mode eksekusi:** C (AI jalankan langsung, dikonfirmasi dev 2026-08-24 — Docker tersedia di sesi Claude Code CLI ini).

| # | Dijalankan setelah fase | Mode | Hasil | Error (kalau fail) | Tanggal |
|---|---|---|---|---|---|
| 1 | A2 + A3 (digabung — A3 tidak butuh perubahan apapun, ACL sudah lengkap sejak 17.0) | C | ❌ Fail | `ImportError: cannot import name 'logging' from 'odoo.tools'` di `personal_email_usage/models/mail.py:6` — lihat DIFF-09/MF-08, TIDAK terdeteksi review statis Step 2/3 | 2026-08-24 |
| 2 | A2 + A3 + A5 (fix DIFF-09 ditambahkan setelah kegagalan #1) | C | ✅ Pass | — (catatan: warning "Model mail.bot is declared but cannot be loaded" muncul di log — pre-existing noise environment `odoo:18.0` image standar, tidak terkait modul ini, `mail_bot` tidak pernah disentuh kode kita) | 2026-08-24 |

---

## Entri

## [Fase A1] Manifest Bootstrap

- **Scope:** `fr_business_directory/__manifest__.py`, `personal_email_usage/__manifest__.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 baris 1-2
- **Aksi:**
  - `fr_business_directory/__manifest__.py`: `'version': '17.0.1.0.0'` → `'version': '18.0.1.0.0'`
  - `personal_email_usage/__manifest__.py`: `'version': '17.0.1.0.0'` → `'version': '18.0.1.0.0'`
- **Secara eksplisit TIDAK dilakukan:** tidak ada perubahan `depends`, `data`, `assets`, atau field manifest lain — manifest tetap merepresentasikan modul penuh (P4)
- **Risiko:** LOW
- **Status:** ✅ Selesai

## [Fase A2] XML Tree → List (Mekanis)

- **Scope:** `fr_business_directory/views/siret_wizard_views.xml`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 (DIFF-01), `02_diff/02_DIFF_ANALYSIS.md` DIFF-01
- **Aksi:**
  - Baris 25: `<field name="result_ids" mode="tree">` → `mode="list"`
  - Baris 26: `<tree string="Results" delete="False" create="false">` → `<list string="Results" delete="False" create="false">` (+ closing tag)
  - Baris 51: `<tree create="false" delete="false" editable="bottom" no_open="1">` → `<list create="false" delete="false" editable="bottom" no_open="1">` (+ closing tag)
- **Secara eksplisit TIDAK dilakukan:** tidak ada perubahan field, atribut lain (`delete`/`create`/`editable`/`no_open`/`decoration-*`), domain, atau context — murni ganti nama tag
- **Risiko:** LOW (mekanis) — tapi item ini yang sebelumnya install-blocking kalau tidak dikerjakan
- **Status:** ✅ Selesai

## [Fase A3] Security Hardening

- **Scope:** `security/ir.model.access.csv` (kedua addon)
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2
- **Aksi:** Tidak ada — dicek langsung, ACL `fr_business_directory` (3 TransientModel: `siret.wizard`, `siret.wizard.result`, `matching.etablissement`) sudah lengkap sejak 17.0. ACL `personal_email_usage` tetap dead file (dikomentari di manifest sejak 17.0, BSL-022) — dibawa apa adanya, TIDAK dihapus (P1).
- **Secara eksplisit TIDAK dilakukan:** tidak menghapus dead ACL file `personal_email_usage`, tidak menambah ACL baru
- **Risiko:** LOW
- **Status:** ✅ Selesai (tidak ada perubahan diperlukan)

## [Fase A4] Skeleton & Folder Integrity

- **Scope:** struktur folder kedua addon
- **Aksi:** Tidak ada — struktur `models/`, `views/`, `security/`, `static/`, `__init__.py` sudah konsisten sejak 17.0, tidak ada folder hilang
- **Risiko:** LOW
- **Status:** ✅ Selesai (tidak ada perubahan diperlukan)

## [Fase A5] Python API Compatibility (Models Only)

- **Scope:** `personal_email_usage/models/mail.py`
- **Item spec (ref):** `03_MIGRATION_SPEC.md` §2 (DIFF-02), `FINDINGS.md` MF-07
- **Aksi:**
  - `fetch_mail(self):` → `fetch_mail(self, raise_exception=True):` (signature diselaraskan dengan core 18.0)
  - Baris terakhir: `super(FetchmailServer, ...).fetch_mail()` → `.fetch_mail(raise_exception=raise_exception)` (teruskan parameter ke path non-IMAP)
- **Secara eksplisit TIDAK dilakukan:** TIDAK mengubah exception handling internal path IMAP (tetap log-only, `except Exception:` polos tanpa `raise_exception` check) — behavior BSL-020/MF-05 (re-fetch tanpa henti) dan BSL-021/MF-06 (log salah hitung) dipertahankan identik sesuai keputusan dev. Tidak menambahkan `import logging` di `siret_wizard.py` (BSL-008/MF-02 tetap dipertahankan, bukan bagian fase ini tapi dicatat supaya tidak dianggap terlewat)
- **Risiko:** LOW (perubahan signature murni, tidak ada perubahan logic) — tapi item ini yang sebelumnya functional-blocking di cron kalau tidak dikerjakan
- **Status:** ✅ Selesai

## [Fase A5 — Addendum] Fix DIFF-09 (ditemukan G1 percobaan #1)

- **Scope:** `personal_email_usage/models/mail.py`
- **Item spec (ref):** `02_diff/02_DIFF_ANALYSIS.md` DIFF-09 (ditambahkan setelah kegagalan G1 #1), `FINDINGS.md` MF-08
- **Aksi:** baris 6: `from odoo.tools import logging` → `import logging` (stdlib langsung, bukan bergantung ke re-export tidak resmi `odoo.tools`)
- **Secara eksplisit TIDAK dilakukan:** tidak ada perubahan lain di file ini di luar baris import ini
- **Risiko:** LOW (import fix mekanis) — tapi ini yang sebelumnya install-blocking (ditemukan lewat G1 nyata, bukan review statis)
- **Status:** ✅ Selesai, diverifikasi G1 percobaan #2 (Pass)

## [Fase B1] Model Risiko Rendah

- **Scope:** semua model kedua addon (`res.partner` extend, `siret.wizard`/`siret.wizard.result`/`matching.etablissement`, `fetchmail.server`/`mail.thread` extend)
- **Aksi:** Tidak ada — dicek langsung, semua `@api.depends` sudah lengkap (`_compute_result_count`, `_compute_activite_principale`, `_compute_etat_administratif_display`), tidak ada onchange, tidak ada constraint custom, relasi (`One2many`/`Many2one`) tidak berubah semantik 17→18
- **Secara eksplisit TIDAK dilakukan:** tidak ada perubahan logic/field baru
- **Risiko:** LOW
- **Status:** ✅ Selesai (tidak ada perubahan diperlukan)

## [Fase C1] View Sederhana (Mekanis)

- **Scope:** `views/menu_item.xml`, `views/partner.xml`, `views/siret_wizard_views.xml`, `views/mail_views.xml`
- **Aksi:** Tree→List sudah dikerjakan di A2 (satu-satunya perubahan mekanis yang diperlukan). Sisa view (menu, form partner xpath, form fetchmail xpath) sudah diverifikasi byte-identical/xpath-valid di Step 2/4 (DIFF-04, DIFF-08) — tidak ada perubahan lagi
- **Secara eksplisit TIDAK dilakukan:** tidak ada perubahan field/layout/domain
- **Risiko:** LOW
- **Status:** ✅ Selesai (perubahan sudah tercakup A2)

## [Fase G2] Validasi Akhir (Runtime)

- **Scope:** verifikasi runtime DIFF-01, DIFF-02, DIFF-09 — bukan full AC sweep (itu Step 9/10)
- **Aksi:**
  - Install (`docker compose up`, G1 percobaan #2): 21 modul termasuk `fr_business_directory` + `personal_email_usage` loaded bersih, tidak ada error/ParseError — membuktikan DIFF-01 (`<tree>`→`<list>`) dan DIFF-09 (`import logging`) valid (kalau salah satu belum di-fix, install akan gagal di titik itu)
  - `odoo shell` langsung terhadap `target_db` yang sudah terinstall: `env['fetchmail.server'].fetch_mail(raise_exception=False)` dipanggil manual → return `True`, tidak ada `TypeError` — membuktikan DIFF-02 (signature `fetch_mail`) valid
- **Catatan:** warning "Model mail.bot is declared but cannot be loaded" muncul di log instalasi — dicek, tidak terkait modul kita (mail_bot adalah modul core, warning ini konsisten muncul di image `odoo:18.0` standar terlepas modul yang di-install)
- **Secara eksplisit TIDAK dilakukan:** tidak ada smoke test UI/browser (tidak ada Owl/JS untuk divalidasi) — full functional AC sweep (AC-01 s/d AC-11) ditunda ke Step 9/10 sesuai scope G2 yang sempit
- **Risiko:** LOW — kedua fix Critical terbukti valid di runtime nyata
- **Status:** ✅ Selesai

---

## Temuan di Luar Spec

- [x] Tidak ada

## Kontribusi ke Knowledge Base

- [x] Tidak ada temuan baru selain yang sudah dicatat di `migration-records/french_business_directory_17.0_18.0/SUMMARY.md` (Step 2, `fetch_mail()` signature)

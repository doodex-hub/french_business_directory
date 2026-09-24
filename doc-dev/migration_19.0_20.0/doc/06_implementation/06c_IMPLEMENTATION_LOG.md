# Implementation Log — french_business_directory

**Step:** 6 — Code Migration
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `migration-tool/templates/06a_CODE_MIGRATION_PHASES.md`
**Tanggal:** 2026-09-24
**Status:** ✅ Selesai (G1 install bersih, 42/42 test PASS, G2 smoke PASS)

> Append only. Satu bagian per fase. Sebutkan eksplisit apa yang SENGAJA TIDAK diubah.

---

## Applicability Check

Sumber: `01a_MIGRATION_INTAKE.md` §2b.

| Fase | Relevan? | Bukti/alasan |
|---|---|---|
| C1 | Ya | `views/partner.xml` (DIFF-03, install-blocking), `siret_wizard_views.xml`, `menu_item.xml`, `mail_views.xml` |
| B2 | Ya (terbatas) | Tulis ke field Json `additional_identifiers` (DIFF-02) — bukan kode 19.0 yang kompleks, tapi mekanisme baru di target |
| C2 | Tidak | Tidak ada `attrs=`/`states=`; ekspresi inline sudah valid (DIFF-11) |
| D1 | Tidak | Tidak ada `controllers/` |
| D2 | Tidak | `'assets': {}`, tidak ada `static/src/` |
| E | Tidak | Tidak ada `.js` |
| F | Tidak | Otomatis N/A (E N/A) |

**Catatan urutan install-blocker modul ini:** blocker tersebar di A3 (ACL, DIFF-01), A5 (import `odoo.osv`, DIFF-04) dan C1 (xpath view partner, DIFF-03) — jadi G1 #1 (setelah A2) dan G1 #2 (setelah A3) DIEKSPEKTASIKAN masih gagal di blocker berikutnya; G1 diulang lagi setelah A5 dan setelah C1 sampai install bersih. Setiap percobaan dicatat.

---

## Tabel Ringkas Status Fase

| Fase | Status | Tanggal |
|---|---|---|
| A1 | ✅ | 2026-09-24 |
| A2 | ✅ (tidak ada perubahan) | 2026-09-24 |
| G1 | lihat tabel Riwayat | 2026-09-24 |
| A3 | ✅ | 2026-09-24 |
| A4 | ✅ (tidak ada perubahan) | 2026-09-24 |
| A5 | ✅ | 2026-09-24 |
| A6 | ✅ (tidak ada perubahan) | 2026-09-24 |
| B1 | ✅ (tidak ada perubahan) | 2026-09-24 |
| B2 | ✅ | 2026-09-24 |
| C1 | ✅ | 2026-09-24 |
| C2 | N/A — Applicability Check | 2026-09-24 |
| D1 | N/A — Applicability Check | 2026-09-24 |
| D2 | N/A — Applicability Check | 2026-09-24 |
| E | N/A — Applicability Check | 2026-09-24 |
| F | N/A — Applicability Check | 2026-09-24 |
| G2 | ✅ | 2026-09-24 |

## Riwayat Percobaan G1 (Install Test)

Mode C (AI jalankan, dikonfirmasi dev di intake 2026-09-24). Environment: `docker-env/` (Odoo 20.0 from source `odoo20` read-only, Postgres 16, `-i fr_business_directory,personal_email_usage --test-enable --test-tags=/fr_business_directory,/personal_email_usage --stop-after-init`), `docker compose down -v` sebelum tiap run.

| # | Dijalankan setelah fase | Mode | Hasil | Error (kalau fail) | Tanggal |
|---|---|---|---|---|---|
| 1 | A2 | C | ❌ Fail (diekspektasikan) | `ModuleNotFoundError: No module named 'odoo.osv'` saat load `personal_email_usage` (DIFF-04) — import Python dimuat sebelum data CSV/XML, jadi blocker ACL belum terlihat | 2026-09-24 |
| 2 | A3 | C | ❌ Fail (diekspektasikan) | Sama dengan #1 (`odoo.osv`) — blocker A5 menutupi hasil A3 | 2026-09-24 |
| 3 | A5 | C | ❌ Fail (diekspektasikan) | `security/ir.access.csv` LOLOS (ACL A3 terbukti); berhenti di `ParseError views/partner.xml` (DIFF-03, xpath `id="company"`) | 2026-09-24 |
| 4 | B2 + C1 (percobaan pertama) | C | ❌ Fail | `Name or id "name" in <label for="..."> must be present in view but is missing` — placeholder `$0` diletakkan bersama teks/child lain di `div`; `template_inheritance.py:163` hanya mengganti elemen yang teksnya PERSIS `$0` → field nama hilang | 2026-09-24 |
| 5 | C1 (perbaikan: dua xpath) | C | ✅ Install bersih — test 0 failed, **2 error** of 32 | `ValidationError: Invalid identifier: 12345678900012 (SIRET)` di `test_select_result_overwrites_partner` & `test_select_department_field_untouched_when_model_absent` — data dummy lama gagal Luhn (MF-06, bukti MF-02 deviasi a) | 2026-09-24 |
| 6 | G2 (test diadaptasi + 10 test baru) | C | ⚠️ 1 failed of 42 | `test_new_partner_form_contacts_context_is_company` — characterization MF-03: nilai teramati `(True, False, True, False)` ≠ tebakan awal `(True, True, True, False)` | 2026-09-24 |
| 7 | G2 (assert dikunci ke nilai teramati) | C | ✅ **0 failed, 0 error of 42 tests** | — | 2026-09-24 |

---

## Entri

## [Fase A1] Manifest Bootstrap

- **Scope:** `fr_business_directory/__manifest__.py`, `personal_email_usage/__manifest__.py`
- **Item spec (ref):** 03 §2 baris manifest, DIFF-08
- **Aksi:**
  - kedua manifest: `'version': '19.0.1.0.0'` → `'20.0.1.0.0'`
- **Secara eksplisit TIDAK dilakukan:** `data` belum diubah (entri ACL diganti di A3), `depends`/`images`/`assets`/`application`/key `company` tidak disentuh, baris `# 'security/ir.model.access.csv'` yang dikomentari di `personal_email_usage` dibiarkan.
- **Risiko:** LOW
- **Status:** ✅ Selesai

## [Fase A2] XML Tree → List

- **Scope:** semua XML kedua addon
- **Aksi:** tidak ada — `grep "<tree\|tree,\|'tree'"` = 0 match (sudah `<list>` sejak migrasi 17→18).
- **Secara eksplisit TIDAK dilakukan:** xpath `views/partner.xml` (DIFF-03) TIDAK disentuh di fase ini (itu C1).
- **Risiko:** LOW
- **Status:** ✅ Selesai

## [Fase A3] Security Hardening

- **Scope:** `fr_business_directory/security/`, `fr_business_directory/__manifest__.py` (entri `data` ACL saja)
- **Item spec (ref):** 03 §2 baris ACL, DIFF-01, MF-01
- **Aksi:**
  - `security/ir.access.csv` (baru): header `id,name,model_id,group_id/id,operation,domain`; 3 baris (`access_siret_wizard`, `access_siret_wizard_result`, `access_matching_etablissements`) — xmlid & name sama dengan 19.0, `model_id` = nama model, `base.group_user`, `operation=crud`, domain kosong (format output konverter native `upgrade_code/19.4-00-ir-access.py`)
  - `security/ir.model.access.csv`: dihapus (`git rm`)
  - manifest `data`: `'security/ir.model.access.csv'` → `'security/ir.access.csv'` (posisi sama)
- **Secara eksplisit TIDAK dilakukan:** `personal_email_usage/security/ir.model.access.csv` (dead file, BSL-022) tidak disentuh; tidak ada grup/domain baru.
- **Risiko:** LOW
- **Status:** ✅ Selesai (terbukti G1 #3)

## [Fase A4] Skeleton & Folder Integrity

- **Aksi:** tidak ada — `__init__.py` kedua addon konsisten dengan isi `models/`/`tests/` (dicek).
- **Status:** ✅ Selesai

## [Fase A5] Python API Compatibility

- **Scope:** `personal_email_usage/models/mail.py`
- **Item spec (ref):** 03 §2, DIFF-04, MF-04
- **Aksi:** hapus baris `from odoo.osv import expression` (satu baris).
- **Secara eksplisit TIDAK dilakukan:** import tak terpakai lain dibiarkan (masih ada di 20.0: `odoo.tools.config`, `odoo.fields.Datetime`, `requests`, dst — dicek); `self._cr`/`self._context` deprecated dibiarkan (MF-05); `_fetch_mail`/`message_new` tidak disentuh (DIFF-06).
- **Risiko:** LOW
- **Status:** ✅ Selesai (terbukti G1 #3)

## [Fase A6] Housekeeping README

- **Aksi:** tidak ada — `README.md` kedua addon dan `LISEZMOI.md` berisi profil Doodex generik, tidak menyebut versi Odoo/instruksi install versi-spesifik.
- **Status:** ✅ Selesai

## [Fase B1] Model Risiko Rendah

- **Aksi:** tidak ada — `res.partner` (`social_reason`, `siret_wizard()`), `siret.wizard` (default_get/fetch/paginasi), compute `matching.etablissement` stabil di 20.0 (02 §0e).
- **Status:** ✅ Selesai

## [Fase B2] Model Kompleks — target SIRET

- **Scope:** `fr_business_directory/models/siret_wizard.py`
- **Item spec (ref):** 03 §2 baris `select_siret`, DIFF-02, MF-02
- **Aksi:**
  - helper modul-level baru `_fr_siret_identifiers(partner, siret)` (salin JSON existing, `pop` `FR_SIRET`/`FR_SIREN`, set `FR_SIRET` kalau truthy)
  - 4 cabang `partner.write()` (result×2, etablissement×2): key `'company_registry': self.siret` → `'additional_identifiers': _fr_siret_identifiers(partner, self.siret)` — posisi key, field lain, dan satu-write-per-select tidak berubah
- **Secara eksplisit TIDAK dilakukan:** tidak ada bypass validasi (`no_vat_validation`), tidak ada perubahan `_fetch_siret_data`/paginasi/compute/bug pre-existing (BSL-008..011), field wizard `siret` tidak di-rename.
- **Risiko:** MEDIUM (deviasi edge-case terdokumentasi MF-02)
- **Status:** ✅ Selesai

## [Fase C1] View Sederhana — partner form

- **Scope:** `fr_business_directory/views/partner.xml`
- **Item spec (ref):** 03 §2 baris view, DIFF-03, MF-03
- **Aksi:** `<field id="company" name="name" position="replace">` diganti dua xpath: (1) `//h1/field[@name='name']` `replace` → `<div style="display: flex; align-items: center;white-space:nowrap">$0</div>` (field nama native 20.0 dibungkus apa adanya, selalu tampil); (2) `//h1/div/field[@name='name']` `after` → tombol `siret_wizard` dengan atribut identik 19.0 (`invisible="is_company != True"`). `record` id/`inherit_id`/`mode`/`priority` tidak berubah. Percobaan pertama (satu xpath, `$0` + tombol di satu div) gagal — lihat G1 #4.
- **Secara eksplisit TIDAK dilakukan:** ekspresi visibilitas tidak diubah (MF-03 `[PERLU-KEPUTUSAN]`); `siret_wizard_views.xml`/`menu_item.xml`/`mail_views.xml` tidak disentuh.
- **Risiko:** MEDIUM (semantik `is_company`)
- **Status:** ✅ Selesai

## [Fase G2] Validasi Akhir

- **Scope:** `fr_business_directory/tests/` + server runtime
- **Aksi:**
  - `test_siret_wizard.py`: data dummy `_siege()['siret']` `12345678900012` → `33417522101010` (placeholder FR_SIRET resmi Odoo 20.0, lolos Luhn); `test_select_result_overwrites_partner` assert `_get_additional_identifier('FR_SIRET')` (MF-06). Intent test tidak berubah.
  - `test_migration_20.py` (baru, 10 test): AC-00-02 (×2), AC-01-01/02/03, AC-04-01 (etablissement + SIRET kosong), AC-04-04, AC-04-05, AC-05-04. `tests/__init__.py` mengimpor file baru.
  - Server runtime (`docker compose run`, tanpa `--test-enable`): `/web/login` 200, `/web/health` 200, 0 ERROR/CRITICAL di log (hanya WARNING `markdown2 is not installed` — environment, bukan modul).
  - **DIFF terkonfirmasi runtime:** DIFF-01 (G1 #3), DIFF-02 (G1 #5, AC-04-04/05), DIFF-03 (G1 #5, AC-01-01), DIFF-04 (G1 #1-#3), DIFF-06 (15 test fetchmail PASS).
- **Temuan G2:** characterization MF-03 — `is_company` partner baru (context Contacts, tanpa VAT) = `True` di form → `False` setelah save → `True` dengan VAT → `False` saat VAT dihapus. Tombol "Business Directory" hilang setelah save untuk company tanpa VAT (di 19.0 tetap tampil). Diteruskan ke dev sebagai keputusan (FINDINGS MF-03).
- **Secara eksplisit TIDAK dilakukan:** tidak ada browser/klik UI (itu Step 10 — STOP wajib, menunggu slot dev).
- **Status:** ✅ Selesai

---

## Temuan di Luar Spec

- [x] Ada — (1) gotcha `$0` harus jadi teks tunggal elemen (G1 #4) — perbaikan implementasi, spec tidak berubah; (2) nilai `is_company` teramati (G1 #6) → FINDINGS MF-03 diperbarui. Tidak ada perubahan scope.

## Kontribusi ke Knowledge Base

- [x] Ada — `migration-records/french_business_directory_19.0_20.0/SUMMARY.md`: CAND-02 diperkuat dengan nilai `is_company` teramati; CAND-05 (gotcha `$0` di `position="replace"`).

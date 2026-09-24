# Code Review — french_business_directory

**Step:** 8 — Code Review (gate)
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`, `06_implementation/06c_IMPLEMENTATION_LOG.md`, `01_intake/01b_BASELINE_SPEC.md`, `FINDINGS.md`
**Odoo Version:** 20.0
**Diff:** `git diff migration/19.0 8dd7b71 -- fr_business_directory personal_email_usage` (+ satu fix PEP 8 di review ini)
**Files reviewed:** `fr_business_directory/{__manifest__.py, models/siret_wizard.py, security/ir.access.csv (baru), security/ir.model.access.csv (dihapus), views/partner.xml, tests/__init__.py, tests/test_siret_wizard.py, tests/test_migration_20.py (baru)}`, `personal_email_usage/{__manifest__.py, models/mail.py}`
**Tanggal:** 2026-09-24
**Status:** ✔️ Lulus gate

---

## A. Issues

**Status skill `odoo-review`:**
- [x] Terinstall (`target-codebase/.claude/skills/odoo-review` + `odoo-guidelines`/`odoo-security`/`odoo-web-guidelines`) & sudah dijalankan — rules pass + merits pass atas setiap hunk.

**Mapping:** manifest → *Manifest*; `.py` → *Imports*, *Naming*, *Recordsets/domains/context*, *Transactions and exceptions*; `ir.access.csv` → *Access rights* (+ `odoo-security`); `partner.xml` → *Views, actions and data records*, *Anchor view inheritance on names, never on position*; `tests/` → *Tests*. Target = 20.0 (rilis) → kode existing dipertahankan gayanya, diff minimal.

| ID | Severity | Kategori | File | Baris | Issue | Rekomendasi |
|---|---|---|---|---|---|---|
| CR-01 | 🔵 Info | Code Quality (PEP 8) | `fr_business_directory/models/siret_wizard.py` | 20-22 | Helper modul-level baru diikuti hanya 1 baris kosong sebelum `class SiretWizard` | ✅ Diperbaiki di review ini (2 baris kosong) — unambiguous, tanpa efek perilaku |
| CR-02 | 🔵 Info | Tests (*judgement*) | `tests/test_migration_20.py`, `test_siret_wizard.py` | — | Guideline menyarankan `BaseCommon` untuk test bisnis baru; file ini memakai `TransactionCase` mengikuti gaya test existing modul (target rilis → gaya file existing menang) | Dibiarkan |
| CR-03 | 🔵 Info | Konvensi (pre-existing, bukan hunk diff) | `personal_email_usage/models/mail.py:137` | 137 | `self._cr.commit()` di dalam loop (guideline *Transactions*: jangan commit tanpa cursor sendiri) + deprecated | Pre-existing BSL-027/MF-05 — dipertahankan (P1 fidelity), bukan temuan diff |
| CR-04 | 🔵 Info | Access rights | `fr_business_directory/security/ir.access.csv` | 2-4 | `crud` ke `base.group_user` untuk 3 TransientModel — tidak ada grant `c/u/d` ke portal/public/everyone; tanpa row group-less (tidak ada risiko lock-out); model tidak multi-company | OK — setara ACL 19.0 |

**Business Logic (manual):** lihat §C — semua rule BSL ter-implementasi setara; deviasi terdokumentasi MF-02 (a,b) & MF-03.

**Consumers yang tidak terlihat di diff (skill §"Code the diff never shows"):**
- `company_registry` — grep kedua addon (termasuk tests, XML, i18n) setelah perubahan: 0 sisa pemakaian kode (hanya di komentar/docstring penjelas migrasi). Sweep `odoo-security` atas hunk diff: tidak ada `sudo`/SQL/route/`eval`/mutable default baru; helper `_fr_siret_identifiers` fungsi modul-level privat (tidak ter-expose RPC).
- `additional_identifiers` sebagai *commercial field*: 19.0 `company_registry` ada di `_commercial_fields()` (`odoo19/.../res_partner.py:693`, disinkron turun ke child); 20.0 `additional_identifiers` ada di `_synced_commercial_fields()` (`odoo20/.../res_partner.py:739`). Select hanya bisa dijalankan dari partner yang `is_company` (entitas komersial sendiri) → propagasi ke child setara. Dicek terhadap `odoo19`/`odoo20` checkout lokal.
- Tidak ada modul lain di addons path yang meng-inherit `fr_business_directory.res_partner_form_inherit` atau memanggil `select_siret` (grep `odoo20/addons` = 0).

## B. Gap Analysis — Implementasi vs Migration Spec

| Spec item | Implementasi | Status | Catatan |
|---|---|---|---|
| DIFF-08 manifest version | kedua manifest `20.0.1.0.0` | ✅ Match | |
| DIFF-01 ACL | `security/ir.access.csv` 3 baris `crud`, file lama dihapus, manifest diganti | ✅ Match | format = output konverter native |
| DIFF-02 SIRET | helper `_fr_siret_identifiers` + 4 cabang write | ✅ Match | opsi 1 MF-02 |
| DIFF-03 view | dua xpath (`replace` `$0` + `after` tombol) | ✅ Match (dengan penyesuaian teknis) | spec awal satu xpath; `$0` gotcha (G1 #4) → dua xpath, hasil DOM sama dengan spec |
| DIFF-04 `odoo.osv` | satu baris dihapus | ✅ Match | |
| DIFF-07 test | fixture SIRET + assertion `FR_SIRET` + 10 test baru | ✅ Match | |
| `docker-env/` | Dockerfile/requirements disalin, compose 20.0 port 8196 | ✅ Match | `--without-demo=all` dihapus (default 20.0 tanpa demo) |

## C. Gap Analysis — Implementasi vs Acceptance Criteria (Desk Review)

| AC ID | Behavior | Status | Jejak Nalar | Catatan |
|---|---|---|---|---|
| AC-00-01 | Install bersih | ✅ | `-i` kedua addon → load `ir.access.csv` → views → tests; G1 #7 0 ERROR | |
| AC-00-02 | ACL crud | ✅ | CSV → `ir.access` (model_id by name) → test `has_access` 4 operasi user internal | |
| AC-01-01 | Tombol + nama | ✅ struktur / 🟡 workaround | form → `<h1><div flex><field name/><button invisible="parent_id"/></div></h1>`; partner tanpa parent (termasuk company tanpa VAT): tombol tampil; kontak anak: tersembunyi | Workaround MF-03 disetujui dev 2026-09-24 (revisi pasca-gate, finding tetap OPEN) |
| AC-01-02 | is_company form baru | ✅ (characterization) | Form context Contacts → True; save tanpa VAT → False | Nilai dikunci test; bahan keputusan MF-03 |
| AC-01-03 | action | ✅ | `siret_wizard()` tidak berubah | |
| AC-02-01, AC-03-* | fetch & paginasi | ✅ | kode `SiretWizard` tidak disentuh; test existing PASS | |
| AC-04-01 | Select → FR_SIRET | ✅ | klik Select → `select_siret` → `partner.write({'additional_identifiers': {..,'FR_SIRET': siret}, name, street, ...})` → `_clean_additional_identifiers` validasi+deduksi → partner form menampilkan identifier SIRET | Satu write, field lain identik 19.0 |
| AC-04-02/03 | departemen | ✅ | cabang `ir.model` search tidak berubah | AC-04-02 skip (model tak ada) |
| AC-04-04 | SIRET invalid | ✅ (deviasi terdokumentasi) | write → `_validate_identifier(..., 'error')` → `ValidationError` → dialog error ke user, partner tidak berubah | MF-02 (a) |
| AC-04-05 | identifier lain utuh, SIREN deduksi | ✅ | helper menyalin dict, pop FR_SIRET/FR_SIREN → `_clean` deduksi SIREN baru | MF-02 (b) |
| AC-05-*, AC-06-01, AC-07-* | status, compute, tracking, bug preserved | ✅ | kode tidak disentuh; test existing PASS | |
| AC-08-*..AC-11-* | fetchmail/message_new | ✅ | hanya baris import dihapus; 14 test P PASS; entry point cron/tombol 20.0 memanggil `_fetch_mail` (02 §0e) | |

## D. Cek Khusus Migrasi — P1 Fidelity

- [x] Ada deviasi, semuanya eksplisit tercatat: MF-02 (a) ValidationError untuk SIRET invalid, (b) `FR_SIREN` terdeduksi — perilaku platform 20.0; MF-03 — visibilitas tombol mengikuti definisi `is_company` 20.0 (ekspresi 19.0 dipertahankan; ESCALATION menunggu dev). Tidak ada bug pre-existing yang diperbaiki, tidak ada refactor di luar wajib.

**Cek tabrakan dengan core (empat arah):**
1. Arah 1: method modul pada model core — `siret_wizard` (res.partner), `message_new` (mail.thread, override sengaja dengan `super()`), `_fetch_mail` (fetchmail.server, override sengaja) — tidak ada tabrakan tak disengaja.
2. Arah 2: field/method modul (`social_reason`, `siret_wizard`, `mark_read`, `processed_message_ids`) vs `odoo20` → 0 definisi baru bernama sama.
3. Arah 3: N/A (tidak ada registry UI JS).
4. Arah 4: N/A untuk registry JS. Catatan fungsional serupa: 20.0 menambah kapabilitas identifier SIRET native di form partner (widget `additional_identifiers`) — modul tidak menduplikasi field SIRET di partner (hanya menulis ke sana), jadi tidak ada tumpang-tindih UI.
- [x] Sudah dicek (keempat arah) — tidak ada tabrakan/tumpang-tindih.

## E. Perubahan Tak Tertelusuri

- [x] Tidak ada — semua hunk tertelusuri ke DIFF-01..08 / MF-01..06; CR-01 (PEP 8) tercatat di sini.

## F. Kontribusi ke Knowledge Base

- [x] Tidak ada temuan baru di luar CAND-01..05 (sudah di `SUMMARY.md`).

## G. Verdict

- Ringkasan Issues: 0 🔴 · 0 🟡 · 4 🔵
- [x] ✅ Lulus — tidak ada 🔴, lanjut ke step 9

**Guidelines read:** Manifest; Imports; Naming and model layout; Recordsets, domains and context; Transactions and exceptions; Access rights; Views, actions and data records; Anchor view inheritance on names, never on position; Tests; odoo-security SKILL (access rows).

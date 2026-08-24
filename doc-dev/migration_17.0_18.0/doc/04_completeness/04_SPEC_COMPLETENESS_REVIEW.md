# Spec Completeness Review — french_business_directory

**Step:** 4 — Spec Completeness Review (gate)
**Ref:** `03_spec/03_MIGRATION_SPEC.md`, `source-codebase` (branch `migration/17.0_source`)
**Tanggal:** 2026-08-24

> Tujuan: pastikan `03_MIGRATION_SPEC.md` mencakup 100% elemen source module — bukan review kualitas kode (itu step 8).

---

## Tabel Cakupan

### `fr_business_directory`

| Elemen source module | Ada di Migration Spec? | Status | Catatan |
|---|---|---|---|
| `__manifest__.py` | Ya, §2 baris 1 | ✅ Covered | Version bump |
| `__init__.py`, `models/__init__.py` | Tidak eksplisit (trivial import) | ✅ Covered | Copy 1:1, tidak ada isi yang butuh strategi — dianggap implisit bersama `models/*.py` |
| `models/partner.py` | Ya, §2 baris "models/partner.py, models/siret_wizard.py (selain fetch_mail)" | ✅ Covered | — |
| `models/siret_wizard.py` | Ya, §2 (DIFF-06/07) | ✅ Covered | — |
| `views/menu_item.xml` | Ya, §2 (ditambahkan saat review ini) | ✅ Covered | Copy 1:1 |
| `views/partner.xml` | Ya, §2 (DIFF-04) | ✅ Covered | — |
| `views/siret_wizard_views.xml` | Ya, §2 (DIFF-01) | ✅ Covered | `<tree>`→`<list>` |
| `security/ir.model.access.csv` | Ya, §2 | ✅ Covered | — |
| `i18n/fr.po` | Ya, §2 (ditambahkan saat review ini) | ✅ Covered | Copy 1:1 |
| `static/description/*`, `googleaeed8a7b9ec156e7.html`, `LICENSE`, `README.md` | Ya, §2 (ditambahkan saat review ini) | ✅ Covered | Non-fungsional |

### `personal_email_usage`

| Elemen source module | Ada di Migration Spec? | Status | Catatan |
|---|---|---|---|
| `__manifest__.py` | Ya, §2 baris 2 | ✅ Covered | Version bump |
| `__init__.py`, `models/__init__.py` | Tidak eksplisit (trivial import) | ✅ Covered | Copy 1:1 |
| `models/mail.py` — `fetch_mail()` | Ya, §2 (DIFF-02) | ✅ Covered | Signature fix wajib |
| `models/mail.py` — `message_new()` | Ya, §2 | ✅ Covered | Copy 1:1 |
| `views/mail_views.xml` | Tidak eksplisit sebelum review ini | ❌ Gap → **diperbaiki di bawah** | Xpath ke `mail.view_email_server_form`, field `attach` — belum ditelusuri stabilitasnya di 18.0 |
| `security/ir.model.access.csv` | Ya, §2 | ✅ Covered | Dead file, dibawa apa adanya |
| `static/description/*`, `googleaeed8a7b9ec156e7.html`, `LICENSE`, `README.md`, `LISEZMOI.md` | Ya, §2 (ditambahkan saat review ini) | ✅ Covered | Non-fungsional |

---

## Gap Ditemukan & Ditutup

### Gap-01 — `personal_email_usage/views/mail_views.xml` belum di-diff terhadap `mail.view_email_server_form` 18.0

Ditemukan saat review ini (bukan di Step 2/3 sebelumnya). Dicek langsung:

- Xpath target: `//field[@name='attach']` pada `mail.view_email_server_form`.
- `native-source` (`odoo17/addons/mail/views/fetchmail_views.xml`) dan `native-target` (`odoo18/addons/mail/views/fetchmail_views.xml`) — field `attach` **tetap ada** di kedua versi form `fetchmail.server` (dikonfirmasi lewat pembacaan langsung).

**Verdict gap:** Tidak ada perubahan diperlukan — xpath tetap valid. Ditambahkan sebagai baris baru di `03_MIGRATION_SPEC.md` §2 (lihat tabel) supaya tercakup penuh:

| File/simbol | Ref `DIFF-NNN` | Strategi migrasi | Risiko | Ref `BSL-NNN` |
|---|---|---|---|---|
| `personal_email_usage/views/mail_views.xml` | DIFF-08 (baru) | Copy 1:1 — xpath `//field[@name='attach']` pada `mail.view_email_server_form` dikonfirmasi tetap ada di `native-target` 18.0 | Rendah | BSL-001 (field `mark_read` UI) |

> Baris DIFF-08 ini juga ditambahkan ke `02_DIFF_ANALYSIS.md` §1 untuk konsistensi rujukan silang.

---

## Verdict

- [x] ✅ **Lulus** — semua elemen Covered (1 gap ditemukan saat review ini, langsung ditutup dengan verifikasi kode + ditambahkan ke `03_MIGRATION_SPEC.md`/`02_DIFF_ANALYSIS.md`). Lanjut ke Step 5.

# Diff & Compatibility Analysis — french_business_directory

**Step:** 2 — Diff & Compatibility Analysis
**Versi:** 19.0 → 20.0
**Tanggal:** 2026-09-24
**Status:** ✅ Selesai
**Ref:** `01_intake/01a_MIGRATION_INTAKE.md`, `01_intake/01b_BASELINE_SPEC.md`, `migration-tool/knowledge/`, `FINDINGS.md`

Sumber pembanding: `native-source` = `D:\Kuncoro\doodex\repo\odoo19` (Community 19.0), `native-target` = `D:\Kuncoro\doodex\repo\odoo20` (Community 20.0, `version_info = (20, 0, 0, FINAL, 0, '')`). Kode modul 19.0 = `git show migration/19.0:<path>`.

---

## 0. Knowledge Base Check

| Sumber | Sudah ada entry? | Lokasi / relevansi |
|---|---|---|
| `version-diffs/19-to-20.md` | Ya (2026-09-24) | Relevan: baris **`ir.model.access.csv`/`ir.rule` → `ir.access.csv`** (→ DIFF-01) dan **ACL `res.partner` self-write `base.group_user`** (tidak dipakai modul — modul tidak punya test security `res.partner`). Tidak relevan: `/web/session/logout`, `logOutItem`, `computeOptionalActiveFields`, pin message (modul tanpa JS). Gotcha operasional dipakai di Step 6/9: tidak ada image `odoo:20.0` resmi (build from source), wajib `down -v` sebelum rerun G1, `--http-interface=0.0.0.0`, Postgres ≥16 (dari `advanced-sales-analysis-migration-20`). |
| `dependency-compat/fetchmail/18-to-19.md` | Ya (pasangan versi sebelumnya) | Konteks MF-03 (18→19). Dicek ulang untuk 20.0 → arsitektur TIDAK dirombak lagi (DIFF-06). |
| `dependency-compat/l10n_fr/18-to-19.md` | Ya (pasangan versi sebelumnya) | Konteks `siret`→`company_registry`. Untuk 20.0 berubah LAGI (DIFF-02) — belum ada entry 19→20. |
| `dependency-compat/mail/18-to-19.md` | Ya | Tidak relevan (`_to_store`/`messageActionsRegistry`/`_bus_send_store` tidak dipakai modul). |
| `dependency-compat/{base,contacts}/19-to-20.md` | Tidak ada | Analisis baru (DIFF-02, DIFF-03). |

## 0b. Gate Community vs Enterprise

- [x] `01a` §2: TIDAK ADA dependency Enterprise (`base`, `contacts`, `l10n_fr`, `mail` — Community). Cukup `native-target` Community. `enterprise20` tidak perlu dianalisis.

## 0c. Gate Transitive Dependency

- [x] Tidak ada `depends` yang dihapus. Catatan: `contacts` 20.0 `depends: ['base_address_extended', 'mail', 'web_hierarchy']` — `base_address_extended` ikut ter-install transitif; modul menulis `street`/`street2`/`zip`/`city` biasa (field base) — tidak ada ketergantungan baru yang perlu dideklarasikan.

## 0d. Gate Grep Menyeluruh — Rename di Knowledge Base

Grep dilakukan ke SELURUH kedua addon (`.py`, `.xml`, `.csv`, termasuk `tests/`):

| Simbol dari knowledge base / pre-scan | Kemunculan | DIFF |
|---|---|---|
| `ir.model.access` (file/model) | `fr_business_directory/security/ir.model.access.csv` + manifest `:22`; `personal_email_usage/security/ir.model.access.csv` (tidak di manifest) | DIFF-01 |
| `company_registry` | `siret_wizard.py:260,275,354,369`; `tests/test_siret_wizard.py:127,135` | DIFF-02, DIFF-07 |
| `id="company"` / `is_company` | `views/partner.xml:10-13`; `tests/test_siret_wizard.py:55` | DIFF-03, DIFF-07 |
| `odoo.osv` | `personal_email_usage/models/mail.py:11` | DIFF-04 |
| `fetch_mail` / `_fetch_mail` / `_connect__` | `mail.py:61,76,163`; `test_fetchmail.py` (banyak) | DIFF-06 (stabil) |
| `_cr` / `_context` | `mail.py:138`; `siret_wizard.py:24,245,251,329,341` | DIFF-05 (stabil, deprecated) |

## 0e. Gate Silent-Regression per Tipe Override

| Override | Kategori | Hasil cek di 20.0 |
|---|---|---|
| `fetchmail.server._fetch_mail(batch_limit=50)` | (a) Python, entry point tidak langsung (cron) | Entry point cron `_fetch_mails()` MASIH memanggil `records...._fetch_mail(**kw)` (`odoo20/addons/mail/models/fetchmail.py:245-259`); tombol manual `fetch_mail()` MASIH `self.ensure_one().check_access('write')` → `self.sudo()._fetch_mail()` lalu raise exception yang dikembalikan (`:237-242`). Signature & tipe return (`Exception | None`) identik 19.0. `_connect__(allow_archived=False)` masih ada (`:179`). Satu-satunya diff file 19→20: `self.env['ir.cron']._rollback_progress()` baru di jalur error per-message worker native (`:308`) — tidak dipakai jalur IMAP custom. **Stabil.** |
| `mail.thread.message_new(msg_dict, custom_values=None)` | (a) Python, entry point tidak langsung (`message_route`/`message_process`) | Body `message_new` 19↔20 identik (diff kosong); masih dipanggil dari `mail_thread.py:1420` (`ModelCtx.message_new(message_dict, custom_values)`). **Stabil.** |
| `res.partner` view inherit (`partner.xml`) | (b) XML xpath | **Rusak** — DIFF-03. |
| `fetchmail.server` view inherit (`mail_views.xml`, `//field[@name='attach']`) | (b) XML xpath | `attach` masih ada di `mail.view_email_server_form` (`odoo20/addons/mail/views/fetchmail_views.xml:79`). **Stabil.** |
| `siret.wizard*.default_get(self, fields)` | (a) Python | `BaseModel.default_get(self, fields)` signature sama (`odoo20/odoo/orm/models.py:1317`). **Stabil.** |
| (c)/(d) Owl patch / registry | — | N/A (tidak ada JS). |

**Kolisi nama arah kedua (field/method yang DIDEFINISIKAN modul vs definisi baru di 20.0):** grep `social_reason`, `siret_wizard`, `mark_read`, `processed_message_ids` ke `odoo20/odoo/addons/base`, `addons/mail`, `addons/contacts`, `addons/l10n_fr` → **0 match**. Tidak ada kolisi.

## 1. Perubahan Native (Core/Enterprise)

| ID | File/simbol modul | Simbol native terkait | Status di target | Dampak | Sumber |
|---|---|---|---|---|---|
| DIFF-01 | `fr_business_directory/security/ir.model.access.csv` + manifest `data` | Model `ir.model.access` (19.0) → `ir.access` (`odoo20/odoo/addons/base/models/ir_access.py:64`), file `ir.access.csv`, header `id,name,model_id,group_id/id,operation,domain`; konverter resmi `odoo20/odoo/upgrade_code/19.4-00-ir-access.py` | **Dihapus** (model lama tidak ada; `convert_csv_import` menurunkan model dari nama file → KeyError) | **Install-blocking** `fr_business_directory`. `personal_email_usage` tidak terdampak (file tidak dimuat, BSL-022) | Knowledge base `19-to-20.md` + analisis baru (konverter native dibaca penuh) — MF-01 |
| DIFF-02 | `siret_wizard.py:260,275,354,369` `partner.write({'company_registry': ...})` | `res.partner.company_registry` (19.0 `odoo19/odoo/addons/base/models/res_partner.py:241`) → dihapus; pengganti `additional_identifiers = fields.Json` (`odoo20/.../res_partner.py:330`) key `FR_SIRET` (`odoo20/odoo/tools/partner_identifiers.py:645`, validasi `stdnum.fr.siret`), `write()` → `_clean_additional_identifiers()` (`res_partner.py:963,1826`: validasi `error`, deduksi `FR_SIREN`). `l10n_fr/views/res_partner_views.xml` (relabel "Siren/Siret") dihapus di 20.0 | **Dihapus + diganti mekanisme baru (behavior validasi berubah)** | **Fitur inti rusak** ("Select" error field tak dikenal) | Analisis baru — MF-02 |
| DIFF-03 | `views/partner.xml:10` `<field id="company" name="name" position="replace">` + `invisible="is_company != True"` | `base.view_partner_form` 19.0: dua field `name` (`id="company"`/`id="individual"`) + radio `company_type`; 20.0 (`odoo20/.../views/res_partner_views.xml:99-135`): satu field `name` di `<h1>` (widget `text`, `placeholder="Name (company or person)"`), `is_company` = computed store `commercial_partner_id == partner and has_vat` (`res_partner.py:366,944-955`) | **Struktur view dirombak + semantik `is_company` berubah** | **Install-blocking** (xpath tidak ketemu) + visibilitas tombol bergantung VAT | Analisis baru — MF-03 |
| DIFF-04 | `personal_email_usage/models/mail.py:11` `from odoo.osv import expression` | package `odoo.osv` | **Dihapus total** (`odoo20/odoo/osv/` tidak ada) | **Install-blocking** `personal_email_usage` (ImportError saat load) | Analisis baru — MF-04 |
| DIFF-05 | `self._cr.commit()` (`mail.py:138`), `self._context.get(...)` (`siret_wizard.py`) | `BaseModel._cr/_context` (`odoo20/odoo/orm/models.py:5388-5401`) | **Tidak berubah** (masih `@deprecated` sejak 19.0) | `DeprecationWarning` saja | Analisis baru — MF-05 |
| DIFF-06 | `fetchmail.server._fetch_mail` / `_connect__` / `fetch_mail` / cron `_fetch_mails` | `odoo20/addons/mail/models/fetchmail.py` | **Tidak berubah** (1 baris tambahan `_rollback_progress()` di worker native) | Tidak ada | Analisis baru (diff file penuh) |
| DIFF-07 | `tests/test_siret_wizard.py:19,55,127-135` | DIFF-02 (`company_registry`), DIFF-03 (`is_company` computed), validasi Luhn `FR_SIRET` | Test fixture/assertion terikat simbol lama | Test gagal (bukan kode produksi) | Analisis baru — MF-06 |
| DIFF-08 | Manifest kedua addon `version: '19.0.1.0.0'` | Loader 20.0 menandai modul versi-major lain `installable=False` (`odoo20/odoo/modules/module.py:501`) | Wajib bump | Modul tidak installable | Konvensi versi (sama seperti migrasi sebelumnya) |
| DIFF-09 | Manifest keys (`images`, `assets`, `application`, `company`) | `_DEFAULT_MANIFEST` 20.0: dihapus `demo_xml`/`init_xml`/`update_xml`/`images_preview_theme`, ditambah `iap_paid_service`/`other_files` | **Tidak berdampak** (modul tidak memakai key yang dihapus; `company` non-standar tetap diabaikan) | Tidak ada | Analisis baru (diff `_DEFAULT_MANIFEST`) |
| DIFF-10 | `res.partner.partner_latitude/partner_longitude`, `street/street2/zip/city/state_id/country_id`, `tracking` pada `res.partner` | `odoo20/.../res_partner.py:359-360` dst | **Tidak berubah** | Tidak ada | Analisis baru |
| DIFF-11 | `menuitem web_icon`, `ir.actions.act_window` `target='new'`, `list` view, `widget='badge'`, `confirm=`, `special="cancel"` | `odoo20/odoo/tools/convert.py:314`, web client | **Tidak berubah** (dicek statis; visual dikonfirmasi Step 10) | Tidak ada | Analisis baru |

## 2. Kompatibilitas Dependency (OCA/Third-Party)

| Dependency | Versi target tersedia? | Sumber cek | Risiko |
|---|---|---|---|
| — (tidak ada OCA/third-party) | — | `01a` §0/§2 | — |
| `res.country.department` (soft, BSL-006) | Tidak terinstall (sama seperti 19.0) | `ir.model` search di test | Rendah — jalur "model tidak ada" yang dites |
| Python `requests`, `stdnum` | Ya (`odoo20/requirements.txt:46,51`) | requirements native | Rendah |

## 3. Temuan Baru — Migration Records

- [x] Kandidat version-diff/dependency-compat ditulis ke `migration-tool/migration-records/french_business_directory_19.0_20.0/SUMMARY.md` (CAND-01 `company_registry`→`additional_identifiers`, CAND-02 form partner/`is_company`, CAND-03 `odoo.osv` dihapus, CAND-04 konfirmasi ke-2 `ir.access` + detail format konverter). TIDAK dipromosikan ke `knowledge/` di step ini.

## 4. Ringkasan Risiko

| Item | Level risiko | Catatan |
|---|---|---|
| DIFF-01 ACL | Tinggi (install-blocking) / fix rendah-risiko | Format dari konverter native; tanpa `ir.rule` → semantik identik |
| DIFF-02 SIRET | **Kritis** / fix sedang | Perubahan mekanisme penyimpanan + validasi; deviasi edge-case (SIRET invalid) terdokumentasi MF-02 |
| DIFF-03 view/`is_company` | Tinggi / fix struktur rendah, semantik **perlu verifikasi** | Step 9 `Form` test + Step 10 visual (MF-03 `[PERLU-KEPUTUSAN]`) |
| DIFF-04 `odoo.osv` | Tinggi (install-blocking) / fix trivial | Hapus satu baris import tak terpakai |
| DIFF-06 fetchmail | Rendah | Stabil — beda dengan 18→19 (MF-03 lama); tetap diverifikasi G1 karena riwayat silent-regression |
| DIFF-07 test | Sedang | Penyesuaian assertion/data, intent sama |
| DIFF-05/08/09/10/11 | Rendah | — |

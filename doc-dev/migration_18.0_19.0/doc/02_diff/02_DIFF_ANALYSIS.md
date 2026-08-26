# Diff & Compatibility Analysis — french_business_directory

**Step:** 2 — Diff & Compatibility Analysis
**Versi:** 18.0 → 19.0
**Tanggal:** 2026-08-26
**Ref:** `01_intake/01a_MIGRATION_INTAKE.md`, `migration-tool/knowledge/`

---

## 0. Knowledge Base Check

| Sumber | Sudah ada entry? | Lokasi |
|---|---|---|
| `version-diffs/18-to-19.md` | Ya — §1 (riset OCA wiki + verifikasi source) dan §1a (temuan project nyata `advanced_sales_analysis`, tidak overlap dengan modul ini — soal `sale.order.line.tax_id`) | `migration-tool/knowledge/version-diffs/18-to-19.md` |
| `dependency-compat/l10n_fr/...`, `dependency-compat/fetchmail/...` | Tidak ada entry untuk dependency spesifik modul ini | — |

Tidak ada entry knowledge base yang langsung cover breaking change modul ini (`fetch_mail()` signature, `siret`→`company_registry`) — keduanya temuan BARU dari project ini, akan dicatat ke `migration-records/` (lihat §3).

## 0b. Gate Community vs Enterprise

- Dependency map (`01a_MIGRATION_INTAKE.md` §2): `base`, `contacts`, `l10n_fr`, `mail` — **tidak ada baris "Native Enterprise"**.
- Kesimpulan: gate ini **N/A** — cukup cek `native-target` (Community, di dalam folder gabungan `enterprise19.0`). Tidak ada kebutuhan cek modul Enterprise spesifik untuk modul ini.

## 0c. Gate Transitive Dependency

- Tidak ada `depends` yang dihapus dari manifest kedua addon di migrasi ini (`base`/`contacts`/`l10n_fr` dan `base`/`mail` tetap sama persis) — gate ini **N/A**.

---

## 1. Perubahan Native (Core/Enterprise)

Semua baris di bawah diverifikasi LANGSUNG dengan membaca `native-source` (`D:\Kuncoro\doodex\repo\odoo18`) vs `native-target` (`D:\Kuncoro\doodex\repo\enterprise19.0`) — bukan dari klaim wiki semata.

| ID | File/simbol modul | Simbol native terkait | Status di target | Dampak | Sumber |
|---|---|---|---|---|---|
| DIFF-01 | `personal_email_usage/models/mail.py:61,156` — override `fetch_mail(self, raise_exception=True)` | `mail.fetchmail.server.fetch_mail()` | **Signature berubah** — 18.0: `fetch_mail(self, raise_exception=True)` (`odoo18/addons/mail/models/fetchmail.py:215`), cron caller `_fetch_mails()` (`:213`) panggil `.fetch_mail(raise_exception=False)`. 19.0: BALIK ke `fetch_mail(self)` TANPA parameter (`enterprise19.0/odoo/addons/mail/models/fetchmail.py:237`), cron caller panggil `.fetch_mail()` polos (tidak ada argumen). | **Breaking, install-jalan-tapi-cron-crash.** Override modul WAJIB diadaptasi ke signature 19.0 (hapus parameter) — lihat `FINDINGS.md` MF-01, `03_MIGRATION_SPEC.md`. | Analisis baru — verifikasi langsung `native-source`/`native-target` |
| DIFF-02 | `fr_business_directory/models/siret_wizard.py:260,354` — `partner.write({'siret': ...})` (2 lokasi) | `l10n_fr.res.partner.siret` | **Field dihapus total** — 18.0: `siret = fields.Char(string='SIRET', size=14)` di `odoo18/addons/l10n_fr/models/res_partner.py:10`. 19.0: field `siret` TIDAK ADA lagi di `l10n_fr` (`enterprise19.0/odoo/addons/l10n_fr/models/res_partner.py` — cuma berisi `l10n_fr_is_french` computed, tidak ada `siret`). Fungsinya dikonsolidasi ke field generik core `company_registry` (`base`, sudah ada sejak 18.0 untuk keperluan lain) — `l10n_fr` 19.0 me-relabel view field itu jadi "Siret" (`enterprise19.0/odoo/addons/l10n_fr/views/res_partner_views.xml:13`) dan `l10n_fr_account` 19.0 memakainya untuk cetak "SIRET: ..." di laporan resmi (`l10n_fr_account/models/base_document_layout.py:13`, `views/report_invoice.xml:6`). | **Breaking, fitur inti modul lumpuh** kalau tidak diadaptasi — `write()` ke field yang tidak ada akan error. Ganti key `'siret'`→`'company_registry'` di kedua lokasi — lihat `FINDINGS.md` MF-02, `03_MIGRATION_SPEC.md`. | Analisis baru — verifikasi langsung `native-source`/`native-target`, dikonfirmasi grep repo-wide `enterprise19.0/odoo/addons/l10n_fr/` (0 match `siret` di kode Python) |
| DIFF-03 | `fr_business_directory/views/partner.xml:10` — `<field id="company" name="name" position="replace">` (xpath by id ke `base.view_partner_form`) | `base.res_partner_views.xml` field `id="company"` | **Tidak berubah secara struktural yang berdampak** — 18.0 punya DUA elemen `id="company"` di view (`odoo18/odoo/addons/base/views/res_partner_views.xml:85,160` — dua varian form). 19.0 cuma punya SATU (`enterprise19.0/odoo/addons/base/views/res_partner_views.xml:48` — varian kedua tampaknya dikonsolidasi/dihapus di redesign Contacts app 19.0). Atribut internal field itu sendiri (`invisible=`, `required=`) juga berubah, tapi modul ini melakukan `position="replace"` (ganti total elemen), jadi atribut lama tidak relevan. | **Tidak breaking** — `position="replace"` tetap valid selama `id="company"` ada minimal satu kali (sekarang malah lebih sederhana, cuma satu match). Tidak perlu perubahan kode. | Analisis baru — verifikasi langsung `native-source`/`native-target` |
| DIFF-04 | `fr_business_directory/views/siret_wizard_views.xml`, `personal_email_usage/views/mail_views.xml` | View syntax `<list>` vs `<tree>`, ekspresi inline vs `attrs=` | **Tidak ada perubahan baru untuk 18→19** — kedua file sudah pakai `<list>` dan ekspresi inline sejak migrasi 17→18 (perubahan itu terjadi di 17.0, bukan 18→19, sesuai peringatan `knowledge/version-diffs/18-to-19.md` §2). | Tidak ada dampak. | Cross-check `knowledge/version-diffs/18-to-19.md` §2 + baca langsung view files |
| DIFF-05 | `personal_email_usage/views/mail_views.xml:8` — `<xpath expr="//field[@name='attach']" position="after">` ke `mail.view_email_server_form` | `mail.fetchmail_views.xml` field `attach` | **Tidak berubah** — field `attach` ada di posisi yang sama (`odoo18/addons/mail/views/fetchmail_views.xml:79`, `enterprise19.0/odoo/addons/mail/views/fetchmail_views.xml:79`). | Tidak ada dampak. | Analisis baru — verifikasi langsung |
| DIFF-06 | `personal_email_usage/models/mail.py` — `mail.thread.message_new()` override, `mail.thread.message_process()` call | `mail.mail_thread.message_new()` / `message_process()` | **Signature tidak berubah** — `message_new(self, msg_dict, custom_values=None)` identik 18.0↔19.0; `message_process(self, model, message, custom_values=None, ...)` identik 18.0↔19.0. | Tidak ada dampak. | Analisis baru — verifikasi langsung `mail_thread.py` |
| DIFF-07 | `personal_email_usage/models/mail.py:131` — `self._cr.commit()` | ORM internal var `self._cr` (OCA wiki: disarankan pindah ke `self.env.cr`) | **Masih ada, alias deprecated** — dikonfirmasi `enterprise19.0/odoo/orm/models.py:5913` (`ORM core dipindah dari `odoo/models.py` ke `odoo/orm/models.py` di 19.0, tapi property `_cr` tetap ada). TIDAK install/runtime-blocking. | Tidak ada dampak fungsional — boleh dibiarkan apa adanya untuk migrasi cepat (port kode saja, tidak wajib cleanup). | Analisis baru — verifikasi langsung `odoo/orm/models.py` |
| DIFF-08 | `res.groups.category_id`→`privilege_id`, `groups_id`→`group_ids` (OCA wiki §1) | `base.res.groups`, `res.users`/`ir.ui.view`/dst | **Tidak relevan ke modul ini** — modul tidak baca/tulis `category_id`/`groups_id` secara programatik (cuma pakai atribut XML statis `groups="base.group_no_one"` di view, mekanisme berbeda dan tidak terdampak). | Tidak ada dampak. | Cross-check `knowledge/version-diffs/18-to-19.md` §1 |
| DIFF-09 | `_sql_constraints`, `odoo.osv.expression`, `@api.returns`, `auto_join`, `name_search override args→domain` (OCA wiki §1) | Berbagai | **Tidak dipakai modul ini** — dicek langsung, tidak ada `_sql_constraints`, tidak ada import `odoo.osv.expression`, tidak ada `@api.returns`, tidak ada `auto_join=True`, tidak ada override `name_search`. | Tidak ada dampak. | Grep repo-wide `source-codebase` |

## 2. Kompatibilitas Dependency (OCA/Third-Party)

| Dependency | Versi target tersedia? | Sumber cek | Risiko |
|---|---|---|---|
| `res.country.department` (soft-dependency opsional, OCA kemungkinan `l10n_fr_department`) | Tidak dicek (tidak di-connect, dikonfirmasi dev tetap dianggap opsional) — kode sudah defensif (`self.env['ir.model'].search(...)` sebelum dipakai), tidak akan crash kalau addon tidak terinstall di 19.0 juga | `01a_MIGRATION_INTAKE.md` §0/§2 | Rendah — behavior defensif sudah menangani ketiadaan addon ini di versi manapun |

## 3. Temuan Baru — Ditulis ke Migration Records

- [x] DIFF-01 (`fetch_mail` signature) → dicatat sebagai kandidat `version-diff` di `migration-tool/migration-records/french_business_directory_18.0_19.0/SUMMARY.md`
- [x] DIFF-02 (`siret`→`company_registry`) → dicatat sebagai kandidat `version-diff` + `dependency-compat/l10n_fr/18-to-19.md` (baru) di file yang sama
- Promosi ke `knowledge/` HANYA lewat sesi curation terpisah — tidak dilakukan di step ini.

## 4. Ringkasan Risiko

| Item | Level risiko | Catatan |
|---|---|---|
| DIFF-01 — `fetch_mail()` signature | Tinggi (tapi mudah diperbaiki) | Fix mekanis satu baris signature + satu baris pemanggilan `super()`, sudah ada preseden identik dari migrasi 17→18 modul ini sendiri |
| DIFF-02 — `siret`→`company_registry` | Tinggi (tapi mudah diperbaiki) | Fix mekanis rename key di 2 lokasi `write()`, tidak ada perubahan logic/value |
| DIFF-03..DIFF-09 | Rendah/Tidak ada | Tidak perlu perubahan kode |
| Dependency OCA opsional (`res.country.department`) | Rendah | Sudah defensif by design |

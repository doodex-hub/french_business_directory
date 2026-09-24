# Baseline Spec — french_business_directory (fr_business_directory + personal_email_usage)

**Step:** 1 — Intake & Scope (pelengkap `01a_MIGRATION_INTAKE.md`)
**Tujuan:** dokumentasikan APA yang modul lakukan (behavior as-is) di 19.0 — bukan bagaimana diimplementasikan.
**Tanggal:** 2026-09-24
**Sumber:** Direkonsiliasi dari `doc-dev/migration_18.0_19.0/doc/01_intake/01b_BASELINE_SPEC.md` (baseline 18.0, BSL-001..024, tervalidasi) + cross-check baris-per-baris ULANG ke kode 19.0 aktual (`git show migration/19.0:<path>`, HEAD `35c4e25`) + 30 test executable yang lulus 30/30 di G1 final 18→19 (`FINDINGS.md` 18→19 MF-04). Nomor baris di bawah = kode 19.0.

> Dua addon independen — Bagian A/B, penomoran `BSL-NNN` kontinu lintas keduanya dan dilanjutkan dari project sebelumnya (traceability). ID lama TIDAK dipakai ulang untuk klaim lain.

---

## Ringkasan untuk Review — Perlu Konfirmasi User

Tally provenance: 20 `[MATCH]` tanpa perubahan, 4 `[MATCH-UPDATED]` (hasil migrasi 18→19 yang sekarang jadi baseline: BSL-004, BSL-006, BSL-015, BSL-023 — intent tidak berubah), 6 `[NO-SPEC]` baru (BSL-025..030, dari baca kode 19.0 — belum pernah didokumentasikan eksplisit), 0 `[GAP]`.

1. **BSL-004/BSL-006 `[MATCH-UPDATED]`** — "Select" menulis SIRET ke `res.partner.company_registry` (Char bebas, TANPA validasi format) — hasil MF-02 project 18→19. **Kritis untuk 20.0:** field ini hilang dari base 20.0 (DIFF-02).
2. **BSL-025 `[NO-SPEC]`** — Tombol + field nama perusahaan dirender lewat `replace` field `<field id="company" name="name">` (yang di 19.0 hanya salah satu dari DUA field `name` — `company`/`individual`); div pengganti `invisible="is_company != True"`, jadi partner individu tetap memakai field `name` native `id="individual"`. `is_company` di 19.0 = boolean biasa yang di-set user lewat radio `company_type`. **Kritis untuk 20.0:** form dirombak (DIFF-03).
3. **BSL-015/BSL-023 `[MATCH-UPDATED]`** — override IMAP ada di `_fetch_mail(batch_limit=50)` (bukan `fetch_mail()`), koneksi via `_connect__()`, delegasi non-IMAP `super()._fetch_mail(batch_limit=batch_limit)` — hasil MF-03 project 18→19.
4. **Bug pre-existing WAJIB dipertahankan (tidak berubah):** BSL-008 (`_logger` tak terdefinisi → `NameError`), BSL-009 (param `limite_matching_etablissements` hilang di Prev), BSL-010 (return `None` implisit), BSL-011 (`print()` debug), BSL-020 (email di-skip di-fetch ulang selamanya, prioritas TINGGI), BSL-021 (log "succeeded" = `count - failed`).
5. **BSL-026 `[NO-SPEC]`** — `from odoo.osv import expression` (dan beberapa import lain) di `mail.py` TIDAK PERNAH dipakai — tidak fungsional di 19.0, tapi install-blocking di 20.0 (DIFF-04).
6. **BSL-027 `[NO-SPEC]`** (catatan MF-04 18→19) — `self._cr.commit()` per email di `_fetch_mail()`, memicu `DeprecationWarning` sejak 19.0 (masih ada, masih deprecated di 20.0 — bukan error).

---

## Provenance Tag

`[MATCH]` = klaim baseline 18.0 dicek ulang ke kode 19.0, cocok. `[MATCH-UPDATED]` = deskripsi teknis diperbarui mengikuti kode 19.0 (hasil adaptasi migrasi 18→19), intent/behavior sama. `[NO-SPEC]` = klaim baru dari baca kode 19.0, tidak ada dokumen lama yang merincinya. `(ref: BR-NN/F-NN/MF-NN)` merujuk spec backfill/project sebelumnya.

---

# Bagian A — `fr_business_directory`

## 1. Tujuan Modul

Menambahkan tombol "Business Directory" di form kontak (khusus kontak Company) yang membuka wizard pencarian data resmi perusahaan Perancis (SIRET/SIREN) lewat API publik `recherche-entreprises.api.gouv.fr`, lalu mengisi field kontak (nama, alamat, kode pos, SIRET, koordinat, dst) dari hasil yang dipilih user. `(ref: BR-latar belakang)`

## 2. Model & Tanggung Jawab

| Model | Tanggung Jawab |
|---|---|
| `res.partner` (`_inherit`) | Field `social_reason`; method `siret_wizard()` membuka wizard |
| `siret.wizard` (Transient) | Wizard utama — fetch hasil pencarian, paginasi |
| `siret.wizard.result` (Transient) | Satu baris hasil (satu perusahaan / siège) |
| `matching.etablissement` (Transient) | Sub-baris etablissement untuk satu hasil |

ACL: `security/ir.model.access.csv` — 3 baris, `base.group_user` CRUD penuh (1,1,1,1) untuk ketiga model transient, tanpa `ir.rule`.

## 3. Field dengan Makna Bisnis

### `res.partner`
- `social_reason` (Char, `tracking=True`) — nama badan usaha resmi, terpisah dari `name`

### `siret.wizard`
- `partner_name`, `page_number` (default 1), `total_pages`, `result_count`, `page_count` (default 1, hanya di-`print`), `result_ids` (One2many)

### `siret.wizard.result` / `matching.etablissement`
- Data mentah API: `siret`, `social_reason`, alamat (`street`/`street2`/`city`/`post_code`/`department`/`region`), koordinat (Char di result, Float di etablissement), tanggal (`date_creation`/`date_debut_activite` Char, `date_fermeture` Date), `etat_administratif` (+ `etat_administratif_display` computed di etablissement), `activite_principale` (+ `computed_activite_principale` di etablissement)

## 4. Business Workflow / State Transition

- `[BSL-001]` `[MATCH]` (ref: BR-01) Tombol "Business Directory" (`siret_wizard()`, `type="object"`, icon `fa-search`, class `oe_stat_button oe_highlight`) hanya muncul untuk kontak Company (`invisible="is_company != True"`). **Lokasi:** `views/partner.xml:10-15`, `models/partner.py:8-18`. Aksi: `ir.actions.act_window` `siret.wizard`, `view_mode=form`, `target=new`, `context={'active_id': self.id}`.
- `[BSL-002]` `[MATCH]` (ref: BR-02) `SiretWizard.default_get()` otomatis fetch halaman 1 (`q=<partner.name url-quoted>`, `page=1`, `per_page=25`, `limite_matching_etablissements=100`) begitu wizard dibuka; `partner_name` diisi `partner.name`. **Lokasi:** `models/siret_wizard.py:21-34`
- `[BSL-003]` `[MATCH]` (ref: BR-03) Paginasi wrap-around: Next di halaman terakhir (`page_number >= total_pages`) → halaman 1; Prev di halaman 1 → halaman `total_pages`. Tiap navigasi `result_ids.unlink()` dulu, lalu fetch, lalu return action yang me-reload wizard yang sama (`res_id=self.id`, `target=new`). **Lokasi:** `models/siret_wizard.py:131-205`
- `[BSL-004]` `[MATCH-UPDATED]` (ref: BR-04, MF-02 18→19) "Select" (level result ATAU etablissement) SELALU overwrite `res.partner` dari `active_id` context: `name`, `company_registry` (= SIRET), `street` (+`street2` di level result; `street2=''` di level etablissement), `social_reason`, `zip`, `city`, `partner_latitude`, `partner_longitude` — dalam SATU `write()`, tanpa merge/cek field existing, dengan dialog konfirmasi UI (`confirm="Are you sure want to overwrite the Data?"`, tombol etablissement). `company_registry` 19.0 = Char bebas (`compute`+`store`+`readonly=False`), nilai APAPUN diterima tanpa validasi format. Return `True`. **Lokasi:** `models/siret_wizard.py:250-285` (result, `company_registry` baris 260/275), `:340-377` (etablissement, baris 354/369)
- `[BSL-005]` `[MATCH]` (ref: BR-06) `etat_administratif` API `'A'` → `'en activité'`, selain itu → `'fermé le'`; level etablissement: `etat_administratif_display` = label + `' ' + date_fermeture` kalau `'fermé le'` dan ada tanggal. Widget `badge` (hijau kalau `'en activité'`, merah selain itu). **Lokasi:** `models/siret_wizard.py:56,73,379-385`, `views/siret_wizard_views.xml:57-60`

## 5. Server-Side Logic dengan Side Effect

- `[BSL-006]` `[MATCH-UPDATED]` (ref: BR-05) **write (select_siret):** kalau `ir.model` punya `res.country.department` (addon eksternal di luar `depends`), `country_department_id`/`state_id`/`country_id` ikut diisi dari lookup kode departemen (level result: `self.department`; level etablissement: `code_postal[:2]`); kalau TIDAK ada, field-field itu tidak disentuh sama sekali (bukan error). Field SIRET yang ditulis = `company_registry` (lihat BSL-004). **Lokasi:** `models/siret_wizard.py:254-284`, `:346-376`
- `[BSL-007]` `[MATCH]` (ref: BR-07) `_compute_activite_principale` (`matching.etablissement`) menerjemahkan HURUF TERAKHIR `result_id.activite_principale` (level siège, BUKAN field etablissement sendiri) untuk `A`/`B`/`Z`/`D`; kode lain ditampilkan mentah; kalau kosong, field tidak di-assign. **Lokasi:** `models/siret_wizard.py:310-324`
- `[BSL-028]` `[NO-SPEC]` Kalau API `results` punya `matching_etablissements` kosong, SATU baris etablissement dibuat dari data `siege` (alamat = `numero_voie + ' ' + libelle_voie`). Result hanya dibuat kalau `nom_complet` DAN `siege.siret` terisi. **Lokasi:** `models/siret_wizard.py:57-91`

## 6. Client-Side Behavior (Views)

- `[BSL-025]` `[NO-SPEC]` View `res_partner_form_inherit` (`inherit_id=base.view_partner_form`, `mode=extension`, `priority=17`): `<field id="company" name="name" position="replace">` — mengganti field nama KHUSUS COMPANY (di 19.0 base punya dua field `name`: `id="company"` untuk company, `id="individual"` untuk individu, masing-masing di-`invisible` berdasar `is_company`) dengan `<div style="display: flex; align-items: center;white-space:nowrap" invisible="is_company != True">` berisi field `name` (`id="company"`, `class="text-break"`, `default_focus="1"`, `placeholder="e.g. Lumber Inc"`, `required="type == 'contact'"`, `invisible="is_company != True"`) + tombol BSL-001. Efek UX: company → nama + tombol sebaris; individu → field nama native, tanpa tombol. `is_company` di 19.0 = Boolean biasa, di-set user via radio `company_type` (Individual/Company). **Lokasi:** `views/partner.xml:1-18`
- Wizard `siret.wizard`: form dialog, judul `<result_count> Results Found`, kontrol paginasi Prev / `page_number / total_pages` / Next, list hasil (`create=false`, `delete=False`), footer Cancel. Form `siret.wizard.result`: list etablissement editable (`create/delete=false`, `no_open`), kolom siret/activite/adresse/date_creation/badge status + tombol Select (dengan confirm). **Lokasi:** `views/siret_wizard_views.xml`
- Menu root `Business Directory` (`menu_business_directory`, `web_icon=fr_business_directory,static/description/icon.png`) TANPA action/child — menu kosong. **Lokasi:** `views/menu_item.xml`
- Tidak ada Owl/JS custom (`'assets': {}`).

## 7. Dependency Eksternal

- Eksplisit: `depends: ['base', 'contacts', 'l10n_fr']`
- Implisit: soft-dependency `res.country.department` (BSL-006); API HTTP publik `https://recherche-entreprises.api.gouv.fr` via `requests` (tanpa API key, tanpa timeout).

## 8. Quirk / Behavior Non-Obvious (WAJIB dipertahankan)

- `[BSL-008]` `[MATCH]` (ref: F-01) `_logger` dipakai (`siret_wizard.py:113,128`) tapi TIDAK PERNAH didefinisikan → `NameError` kalau `siege` dict valid tapi `nom_complet`/`siret` kosong, atau `requests.RequestException`. `siege` bukan dict → result di-skip tanpa log.
- `[BSL-009]` `[MATCH]` (ref: F-02) `fetch_previous_page` (baris 177 & 195) TANPA `&limite_matching_etablissements=100`; `fetch_next_page` (baris 140/156) DENGAN.
- `[BSL-010]` `[MATCH]` (ref: F-03) `fetch_next_page`/`fetch_previous_page`: `partner_name` falsy di kondisi navigasi valid → return `None` implisit (tombol tanpa efek).
- `[BSL-011]` `[MATCH]` (ref: F-04) `print(...)` debug tertinggal (`siret_wizard.py:141,157,178,192,196`).
- `[BSL-012]` `[MATCH]` (ref: F-06) File `googleaeed8a7b9ec156e7.html` di root addon — housekeeping.
- `[BSL-013]` `[MATCH]` (ref: BR-08) `social_reason` `tracking=True` — perubahan tercatat di chatter. **Lokasi:** `models/partner.py:6`
- `[BSL-014]` `[MATCH]` `siret_wizard()` method BARU (bukan override).
- `[BSL-029]` `[NO-SPEC]` `.get('date_fermeture', '')` pada etablissement yang tidak punya key itu → field Date diisi `''` → di 19.0 TIDAK crash (tersimpan falsy) — CAND-04 project 18→19, dikunci test `test_matching_etablissement_missing_date_fermeture_key_no_longer_crashes`.
- `[BSL-030]` `[NO-SPEC]` `self._context.get('active_id')` (akses `_context` — deprecated sejak 19.0, bukan error) di `default_get`/`select_siret`. **Lokasi:** `models/siret_wizard.py:24,245,251,329,341`

---

# Bagian B — `personal_email_usage`

## 1. Tujuan Modul

Kontrol lanjutan fetch email masuk IMAP `fetchmail.server`: (1) pilihan menandai email fetched read/unread di server, (2) skip email dari user internal, (3) hanya proses email dari pengirim yang sudah jadi kontak, (4) dedup via `Message-ID`, (5) blokir auto-create partner dari email masuk. Tidak menyentuh outgoing.

## 2. Model & Tanggung Jawab

| Model | Tanggung Jawab |
|---|---|
| `fetchmail.server` (`_inherit`) | Field `mark_read`, `processed_message_ids`; override total `_fetch_mail()` untuk server IMAP |
| `mail.thread` (`_inherit`, Abstract) | Override `message_new()` — blokir auto-create `res.partner` |

## 3. Field dengan Makna Bisnis

- `mark_read` (Boolean, default `False`) — tandai email fetched sebagai read di server
- `processed_message_ids` (Text) — `Message-ID` yang sudah diproses, dipisah koma

## 4. Business Workflow / State Transition

- `[BSL-015]` `[MATCH-UPDATED]` (ref: BR-02, MF-03 18→19) `_fetch_mail(self, batch_limit=50)` di-override TOTAL untuk `server_type == 'imap'` (loop raw imaplib: `_connect__()` → `select()` → `search(None, '(UNSEEN)')` → per email `fetch(num, '(RFC822)')`), TIDAK memanggil `super()` untuk grup IMAP. Non-IMAP → `super(...)._fetch_mail(batch_limit=batch_limit)`. Terpanggil baik dari cron (`_fetch_mails()` → `_fetch_mail()`) maupun tombol manual (`fetch_mail()` wrapper core → `sudo()._fetch_mail()`). **Lokasi:** `models/mail.py:61-163`
- `[BSL-016]` `[MATCH]` (ref: BR-04) Skip kalau `from_email` cocok `res.users` (`login =ilike`, `share=False`). **Lokasi:** `models/mail.py:94-103`
- `[BSL-017]` `[MATCH]` (ref: BR-05) Bukan user internal → skip juga kalau tidak ada `res.partner` dengan `email =ilike from_email`. **Lokasi:** `models/mail.py:105-114`
- `[BSL-018]` `[MATCH]` (ref: BR-06) Email lolos → `mail.thread.with_context(fetchmail_cron_running=True, default_fetchmail_server_id=server.id).message_process(server.object_id.model, raw, save_original=server.original, strip_attachments=(not server.attach))`; exception per email di-log dan dihitung `failed`, batch lanjut. **Lokasi:** `models/mail.py:116-136`
- `[BSL-019]` `[MATCH]` (ref: BR-07) `message_new()`: model target `res.partner` → kembalikan partner existing (`email =ilike`, limit 1) atau `False` (TIDAK PERNAH buat partner baru); model lain → `super()`. **Lokasi:** `models/mail.py:22-43`

## 5. Server-Side Logic dengan Side Effect

- `[BSL-020]` `[MATCH]` (ref: F-07, **prioritas TINGGI**) Tiap email langsung `-FLAGS \Seen` setelah fetch, `+FLAGS \Seen` HANYA kalau `mark_read=True`; `message_id` masuk `processed_ids` HANYA di jalur sukses (`res_id` truthy). Email yang di-skip (user internal/non-kontak) atau gagal tidak pernah tercatat → dengan `mark_read=False` di-fetch ulang tiap cron selamanya. Cek dedup terjadi SETELAH flag di-set. **Lokasi:** `models/mail.py:82-92,127-131`
- `[BSL-021]` `[MATCH]` (ref: F-08) Log ringkasan "succeeded" = `count - failed` (under-count). **Lokasi:** `models/mail.py:145-148`
- `[BSL-027]` `[NO-SPEC]` (ref: MF-04 18→19) `self._cr.commit()` setelah TIAP email (termasuk yang gagal, tidak termasuk yang di-skip via `continue`); `processed_message_ids` ditulis sekali per server setelah loop. Kegagalan koneksi/umum per server di-log dan server berikutnya tetap diproses; `close()`/`logout()` di `finally`. **Lokasi:** `models/mail.py:138,140-160`

## 6. Client-Side Behavior (Views)

- `mark_read` di form `fetchmail.server` setelah field `attach`, `groups="base.group_no_one"`. **Lokasi:** `views/mail_views.xml`

## 7. Dependency Eksternal

- Eksplisit: `depends: ['base','mail']`. Implisit: library standar `email`/`imaplib` (lewat `_connect__`).

## 8. Quirk / Behavior Non-Obvious (WAJIB dipertahankan)

- `[BSL-022]` `[MATCH]` (ref: F-09) `security/ir.model.access.csv` mereferensikan model tak ada (`personal_email_usage.personal_email_usage`); baris manifest-nya dikomentari → tidak pernah dimuat. Dead file.
- `[BSL-023]` `[MATCH-UPDATED]` (ref: F-11, MF-03 18→19) Override `_fetch_mail()` TIDAK memanggil `super()` untuk server IMAP — SENGAJA. Return value: `super()._fetch_mail()` untuk sisa non-IMAP (`None` kalau sukses/kosong).
- `[BSL-024]` `[MATCH]` (ref: F-10) `googleaeed8a7b9ec156e7.html` duplikat — housekeeping.
- `[BSL-026]` `[NO-SPEC]` Import tidak terpakai di `models/mail.py:1-13`: `UserError`, `ValidationError`, `requests`, `urllib.parse`, `datetime/timedelta/date`, `relativedelta`, `Datetime`, `re`, **`from odoo.osv import expression`**, `traceback`, `Markup`. Tidak fungsional di 19.0.
- Manifest: `'application': True`, `'category': 'Discuss'`, key non-standar `'company': "Doodex"` (diabaikan Odoo).

---

## Cara Pakai

ID `BSL-NNN` dirujuk wajib di `03_MIGRATION_SPEC.md` dan `05a_MIGRATION_ACCEPTANCE_CRITERIA.md`. Bug pre-existing (BSL-008/009/010/011/020/021) **tidak diperbaiki**. BSL-004/006 (target field SIRET), BSL-025 (struktur view/semantik `is_company`), BSL-026 (import `odoo.osv`) dan ACL Bagian A §2 **WAJIB diadaptasi teknis** untuk 20.0 — intent/behavior fungsional dipertahankan sedekat mungkin, deviasi yang tidak terhindarkan dicatat eksplisit di `FINDINGS.md`.

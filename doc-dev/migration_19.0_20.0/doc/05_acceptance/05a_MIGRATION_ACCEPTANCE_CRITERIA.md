# Migration Acceptance Criteria — french_business_directory

**Step:** 5 — Acceptance Criteria & Test Plan
**Ref:** `01_intake/01b_BASELINE_SPEC.md` dan kode 19.0 yang berjalan — bukan `03_spec/03_MIGRATION_SPEC.md`
**Tanggal:** 2026-09-24
**Status:** ✅ Selesai

> ID AC dipertahankan sama dengan project 17→18 dan 18→19 (traceability lintas project; test existing merujuk ID ini). Perubahan isi karena platform 20.0 ditandai `[COMPAT-FIX WAJIB]`; AC baru untuk pasangan versi ini ditandai `[BARU-20.0]`.
>
> **Catatan ID ganda warisan:** test email lama memakai label `AC-03-01/AC-03-02 [TC-FLAG-01]` untuk `mark_read` — itu BUKAN AC-03 paginasi di bawah; di dokumen ini keduanya dipetakan ke **AC-11-03/AC-11-04**.

---

# Bagian A — `fr_business_directory`

## AC-00 — Instalasi (baru, gate teknis)

**AC-00-01** `[BARU-20.0]` (verifies semua BSL Bagian A/B; `DIFF-01`, `DIFF-03`, `DIFF-04`, `DIFF-08`)
Given database Odoo 20.0 kosong tanpa demo data
When `fr_business_directory` dan `personal_email_usage` di-install bersamaan
Then install bersih tanpa ERROR/CRITICAL di log (tidak ada KeyError `ir.model.access`, xpath error, ImportError)

**AC-00-02** `[COMPAT-FIX WAJIB]` (verifies 01b Bagian A §2 ACL; `DIFF-01`, `MF-01`)
Given modul terinstall
When `ir.access` dibaca untuk `siret.wizard`, `siret.wizard.result`, `matching.etablissement`
Then masing-masing tepat satu record grup `base.group_user`, `operation = 'crud'`, domain kosong — user internal bisa create/read/write/unlink ketiga model (setara `1,1,1,1` 19.0)

## AC-01 — Tombol & Buka Wizard

**AC-01-01** `[COMPAT-FIX WAJIB]` (verifies `BSL-001`, `BSL-025`; `DIFF-03`, `MF-03`)
Given kontak TANPA parent (19.0: kontak dengan `is_company = True`)
When form partner dibuka
Then field nama DAN tombol "Business Directory" tampil sebaris di header. **Update 2026-09-24 (MF-03 workaround, disetujui dev):** tombol tampil untuk semua partner TANPA parent (`invisible="parent_id"`), termasuk company tanpa VAT; kontak anak tidak mendapat tombol. Deviasi terdokumentasi dari 19.0 (19.0: hanya `is_company`); MF-03 CLOSED — aturan diterima dev 2026-09-25 (opsi A). **Alasan:** `is_company` 20.0 dihitung platform (entitas komersial sendiri + punya VAT) sehingga ekspresi 19.0 membuat company tanpa VAT kehilangan tombol setelah save. Konfirmasi visual Step 10.

**AC-01-02** `[BARU-20.0]` (verifies `BSL-001`)
Given form partner baru dibuka lewat action Contacts (`default_is_company: True`), tanpa VAT
When form tampil (sebelum disimpan)
Then nilai `is_company` yang menentukan visibilitas tombol dicatat apa adanya (characterization) — hasilnya jadi bukti untuk keputusan MF-03

**AC-01-03** (verifies `BSL-001`)
Given tombol "Business Directory" diklik
When aksi `siret_wizard()` dieksekusi
Then action `ir.actions.act_window` `siret.wizard` form `target='new'` dengan `context.active_id` = partner

## AC-02 — Auto-Fetch Saat Wizard Dibuka

**AC-02-01** (verifies `BSL-002`)
Given partner company bernama X, tombol diklik
When wizard terbuka
Then request otomatis ke `recherche-entreprises.api.gouv.fr` dengan `q=X&page=1&per_page=25&limite_matching_etablissements=100`, hasil halaman 1 langsung terisi

## AC-03 — Paginasi

**AC-03-01** (verifies `BSL-003`) Given wizard di halaman terakhir, When "Next", Then kembali ke halaman 1, hasil lama di-unlink dulu.
**AC-03-02** (verifies `BSL-003`) Given halaman 1, When "Prev", Then lompat ke halaman terakhir.
**AC-03-03** `[PRESERVE-BUG]` (verifies `BSL-009`) Given navigasi "Prev", When request dikirim, Then TANPA `limite_matching_etablissements`.
**AC-03-04** `[PRESERVE-BUG]` (verifies `BSL-010`) Given `partner_name` falsy, When Next/Prev dalam kondisi valid, Then return `None` implisit tanpa error.

## AC-04 — Select Hasil Pencarian

**AC-04-01** `[COMPAT-FIX WAJIB]` (verifies `BSL-004`; `DIFF-02`, `MF-02`)
Given "Select" pada baris hasil (level `siret.wizard.result` ATAU `matching.etablissement`) dengan SIRET valid, dialog konfirmasi disetujui
When method dijalankan
Then partner (`active_id`) di-overwrite dalam satu write: `name`, **SIRET di `additional_identifiers['FR_SIRET']`** (19.0: `company_registry`), `street` (+`street2` di level result / `''` di level etablissement), `social_reason`, `zip`, `city`, `partner_latitude`, `partner_longitude`; nilai SIRET terbaca lewat `_get_additional_identifier('FR_SIRET')`

**AC-04-02** (verifies `BSL-006`) Given `res.country.department` TERSEDIA, When Select, Then `country_department_id`/`state_id`/`country_id` terisi. *(skip otomatis — model tidak tersedia di environment manapun)*
**AC-04-03** (verifies `BSL-006`) Given `res.country.department` TIDAK tersedia, When Select, Then field departemen/state/country tidak disentuh, field lain tetap ter-write.

**AC-04-04** `[BARU-20.0]` (verifies `BSL-004`; `MF-02` deviasi a — opsi B disetujui dev 2026-09-25)
Given baris hasil dengan SIRET yang TIDAK valid menurut validator native 20.0 (`stdnum.fr.siret`, Luhn)
When "Select"
Then `UserError` berbahasa Inggris "The company directory returned an invalid SIRET (…). The contact was not updated." (partner tidak berubah). **Deviasi terdokumentasi** dari 19.0 (19.0 menyimpan nilai apa adanya).

**AC-04-05** `[BARU-20.0]` (verifies `BSL-004`; `MF-02` deviasi b)
Given partner yang sudah punya identifier lain di `additional_identifiers` (bukan `FR_SIRET`/`FR_SIREN`) dan `FR_SIRET` lama
When "Select" dengan SIRET baru
Then `FR_SIRET` = SIRET baru, `FR_SIREN` = 9 digit pertama SIRET baru (deduksi native), identifier lain TIDAK berubah

## AC-05 — Status & Tampilan

**AC-05-01** (verifies `BSL-005`) `'A'` → "en activité", badge hijau.
**AC-05-02** (verifies `BSL-005`) selain `'A'` → "fermé le [tanggal]", badge merah.
**AC-05-03** (verifies `BSL-007`) huruf terakhir `activite_principale` siège `A/B/Z/D` → label Perancis; lainnya mentah.
**AC-05-04** (verifies `BSL-028`) Given result tanpa `matching_etablissements`, Then satu etablissement dibuat dari data siège.

## AC-06 — Field & Tracking

**AC-06-01** (verifies `BSL-013`) `social_reason` `tracking=True`.

## AC-07 — Quirk Pre-Existing (WAJIB dipertahankan)

**AC-07-01** `[FIX-DISETUJUI-DEV 2026-09-24, RMV-03]` (verifies `BSL-008` — deviasi disengaja dari 19.0) Given respons API tanpa `nom_complet`/`siret`, Then hasil itu di-log warning dan di-skip (bukan `NameError`). Given `RequestException`: HTTP 429 dicoba ulang maks. 2x mengikuti `Retry-After` (≤5 dtk); kalau tetap gagal, Then `UserError` berbahasa Inggris ("…is busy right now…" untuk 429, "…could not be reached…" untuk error lain), bukan traceback.

**AC-07-04** `[FIX-DISETUJUI-DEV 2026-09-24, RMV-06]` Given wizard sudah terbuka, When disimpan (klik tombol pertama), Then API TIDAK dipanggil ulang; `total_pages`/`result_count`/`page_number` tetap benar.

**AC-07-05** `[FIX-DISETUJUI-DEV 2026-09-24, RMV-02]` (verifies `BSL-004` — deviasi disengaja dari 19.0) Given wizard dipaginasi (Next/Prev), When Select, Then yang ditimpa adalah kontak asal (`active_id` awal), BUKAN partner ber-id = id wizard.
**AC-07-02** (verifies `BSL-014`) Tidak ada kolisi `siret_wizard`/`social_reason` dengan core 20.0 (dicek 02 §0e: 0 match).
**AC-07-03** `[PRESERVE-BUG]` (verifies `BSL-029`) Etablissement tanpa key `date_fermeture` tidak crash, `date_fermeture` falsy.

---

# Bagian B — `personal_email_usage`

## AC-08 — Routing Fetch per Tipe Server

**AC-08-01** (verifies `BSL-015`) Given server IMAP, When `fetch_mail()` (manual) atau cron, Then logic custom modul yang jalan, tanpa `super()` untuk server ini.
**AC-08-02** (verifies `BSL-015`) Given server non-IMAP, Then didelegasikan ke `super()._fetch_mail(batch_limit=...)`.
**AC-08-03** `[COMPAT-FIX, stabil]` (verifies `BSL-015`, `BSL-023`; `DIFF-06`)
Given cron 20.0 `_fetch_mails()` memanggil `records._fetch_mail(**kw)` dan tombol memanggil `fetch_mail()` → `sudo()._fetch_mail()`
When dipanggil tanpa argumen / pada recordset kosong
Then tidak ada `TypeError`, return `None` saat sukses — override `_fetch_mail(batch_limit=50)` tetap jadi titik yang terpanggil (tidak ada silent-regression seperti MF-03 18→19)

## AC-09 — Filter Pengirim

**AC-09-01** (verifies `BSL-016`) email dari user internal → skip.
**AC-09-02** (verifies `BSL-017`) bukan user & bukan kontak → skip.
**AC-09-03** (verifies `BSL-018`) kontak dikenal → `message_process(model, raw, save_original, strip_attachments=not attach)` dengan context `fetchmail_cron_running`/`default_fetchmail_server_id`.

## AC-10 — Blokir Auto-Create Partner

**AC-10-01** (verifies `BSL-019`) pengirim match → partner existing dikembalikan.
**AC-10-02** (verifies `BSL-019`) pengirim tidak match → `False`, tidak ada partner baru.
**AC-10-03** (verifies `BSL-019`) model target bukan `res.partner` → `super()`.

## AC-11 — Quirk & Kontrol Flag

**AC-11-01** `[PRESERVE-BUG, prioritas TINGGI]` (verifies `BSL-020`) email di-skip tidak pernah masuk `processed_ids` → di-fetch ulang.
**AC-11-02** `[PRESERVE-BUG]` (verifies `BSL-021`) log "succeeded" = `count - failed`.
**AC-11-03** (verifies `BSL-020`; label test lama `AC-03-01 [TC-FLAG-01]`) `mark_read=True` → `+FLAGS \Seen` diterapkan ulang.
**AC-11-04** (verifies `BSL-020`; label test lama `AC-03-02 [TC-FLAG-01]`) `mark_read=False` → `-FLAGS \Seen` selalu, tanpa `+FLAGS`.
**AC-11-05** (verifies `BSL-027`) duplikat `Message-ID` yang sudah processed di-skip; exception di satu email tidak menghentikan batch; kegagalan koneksi satu server tidak memblokir server lain; `attach` → `strip_attachments`.

---

## Ringkasan Traceability

30 `BSL-NNN` → 33 AC. Housekeeping murni tanpa AC: BSL-011 (print), BSL-012/024 (file google), BSL-022 (dead csv — tercakup AC-00-01 install bersih), BSL-026 (tercakup AC-00-01), BSL-030 (deprecated `_context` — tercakup semua AC wizard). AC berubah isi: AC-01-01, AC-04-01, AC-08-03. AC baru 20.0: AC-00-01/02, AC-01-02, AC-04-04/05 (+ AC-01-03, AC-05-04, AC-07-03, AC-11-03..05 yang memformalkan test existing).

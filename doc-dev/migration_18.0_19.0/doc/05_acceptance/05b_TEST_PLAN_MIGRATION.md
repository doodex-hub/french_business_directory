# Test Plan (Migrasi) — french_business_directory

**Step:** 5 — Acceptance Criteria & Test Plan
**Ref:** `05_acceptance/05a_MIGRATION_ACCEPTANCE_CRITERIA.md`
**Tanggal:** 2026-08-26

> Tidak ada komponen Owl/JS di modul ini — kolom "Tour" selalu N/A.

---

## Step 9 — Dev Testing

> Eksekusi: otomatis/background — `odoo-bin -i fr_business_directory,personal_email_usage --test-enable --test-tags /fr_business_directory,/personal_email_usage --stop-after-init`.

**Catatan audit kesiapan test (9a) — BEDA dari project 17.0→18.0:** modul ini SUDAH punya `tests/test_siret_wizard.py` (14 test) dan `tests/test_fetchmail.py` (9 test) hasil Step 9 project migrasi 17.0→18.0 sebelumnya (23 test terverifikasi lulus saat itu, bagian dari 28 test yang disebut commit gate Step 9 17→18). Ini BUKAN test baru yang ditulis dari nol — melainkan **regression suite yang di-reuse**, dengan **2 test WAJIB diupdate** (lihat `03_MIGRATION_SPEC.md` §2, ditemukan Step 4): `test_select_result_overwrites_partner` (assertion field target) dan `test_fetch_mail_accepts_raise_exception_kwarg` (signature, perlu ditulis ulang jadi `test_fetch_mail_accepts_no_args`). 21 test lain di-reuse APA ADANYA sebagai regression check (memverifikasi behavior yang TIDAK berubah tetap identik di 19.0).

| AC | Deskripsi | Test existing | Status untuk 19.0 |
|---|---|---|---|
| AC-01-01 | Tombol muncul hanya untuk company | — (dicek lewat AC-02-01 setup + code review view) | Reuse — tidak ada test unit terpisah, sama seperti 17→18 |
| AC-02-01 | Auto-fetch saat wizard dibuka | `test_auto_fetch_on_wizard_open` | Reuse apa adanya |
| AC-03-01/02 | Paginasi wrap-around | `test_pagination_wraparound_next`, `test_pagination_wraparound_prev` | Reuse apa adanya |
| AC-03-03 | `[PRESERVE-BUG]` param hilang di Prev | `test_prev_page_missing_limite_param_preserved_bug` | Reuse apa adanya |
| AC-03-04 | `[PRESERVE-BUG]` no-op partner_name kosong | `test_empty_partner_name_is_noop` | Reuse apa adanya |
| AC-04-01 | `[COMPAT-FIX]` Select overwrite partner — field `company_registry` | `test_select_result_overwrites_partner` | **WAJIB update** — assertion `self.partner.siret` → `self.partner.company_registry` |
| AC-04-02 | Select isi department (kalau model ada) | `test_select_department_field_filled_when_model_present` (skip kalau model tidak ada, sama seperti 17→18) | Reuse apa adanya |
| AC-04-03 | Select TIDAK isi department (model tidak ada) | `test_select_department_field_untouched_when_model_absent` | Reuse apa adanya |
| AC-05-01/02 | Badge status administratif | `test_status_label_active`, `test_status_label_closed` | Reuse apa adanya |
| AC-05-03 | Terjemahan kode aktivitas | `test_activite_principale_translation_known_code`, `test_activite_principale_translation_unknown_code_passthrough` | Reuse apa adanya |
| AC-06-01 | `social_reason` tracking | `test_social_reason_field_tracked` | Reuse apa adanya |
| AC-07-01 | `[PRESERVE-BUG]` NameError `_logger` | `test_logger_undefined_nameerror_preserved_bug` | Reuse apa adanya |
| AC-07-02 | Tidak ada method collision | ✓ (install test bersih, lihat G1) | — |
| AC-08-01/02 | Routing fetch per tipe server | (tercakup dalam test lain — `test_skip_email_from_internal_user` dkk memakai server IMAP; tidak ada test eksplisit POP, sama seperti 17→18) | Reuse apa adanya |
| AC-08-03 | `[COMPAT-FIX]` `fetch_mail()` TANPA argumen tidak `TypeError` | `test_fetch_mail_accepts_raise_exception_kwarg` | **WAJIB tulis ulang** jadi `test_fetch_mail_accepts_no_args` — panggil `fetch_mail()` tanpa argumen |
| AC-09-01/02/03 | Filter pengirim (internal/non-kontak/valid) | `test_skip_email_from_internal_user`, `test_skip_email_from_non_contact`, `test_process_email_from_known_contact` | Reuse apa adanya |
| AC-10-01/02 | `message_new()` blokir auto-create | `test_message_new_returns_existing_partner`, `test_message_new_returns_false_for_unknown_sender` | Reuse apa adanya |
| AC-10-03 | `message_new()` delegasi model lain | — (tidak ada test eksplisit, sama seperti 17→18 — diverifikasi code review) | Reuse apa adanya |
| AC-11-01 | `[PRESERVE-BUG]` re-fetch tanpa henti | `test_skipped_email_never_marked_processed_preserved_bug`, `test_processed_email_recorded_in_processed_ids` (control) | Reuse apa adanya |
| AC-11-02 | `[PRESERVE-BUG]` log salah hitung | — (tidak ada test eksplisit assert isi log, sama seperti 17→18) | Reuse apa adanya |
| — | `test_matching_etablissement_missing_date_fermeture_key_crashes` (MF-09 dari project 17→18 — bug pre-existing tambahan, bukan di `01b_BASELINE_SPEC.md` versi ini) | Reuse apa adanya — regression check bug pre-existing lain |

## Step 10 — QA Testing

| AC | Deskripsi | Manual | AI-interaktif | AI+tool eksternal |
|---|---|---|---|---|
| AC-01-01, AC-02-01, AC-03-*, AC-04-* | Alur wizard SIRET end-to-end | ✓ | ✓ (Claude in Chrome, kalau tersedia) | — |
| AC-04-02 | Select dengan `res.country.department` tersedia | ✓ (kalau QA punya akses instance dengan addon OCA terinstall) | — | — |
| AC-05-*, AC-06-01 | Tampilan badge, tracking chatter | ✓ | ✓ | — |
| AC-08-*, AC-09-*, AC-10-* | Fetch email end-to-end (perlu mailbox IMAP test nyata) | ✓ (QA setup mailbox test) | — | ✓ (script Python simulasi IMAP kalau QA tidak punya akses mailbox nyata) |
| AC-11-01 | Verifikasi re-fetch tanpa henti (regresi, bukan bug baru) | ✓ (jalankan cron 2x manual, screenshot log) | — | — |

## Step 11 — UAT

| Kelompok fitur | AC tercakup | UAT |
|---|---|---|
| Pencarian & isi data perusahaan Perancis (SIRET) | AC-01 s/d AC-07 | Business user cari & isi data kontak company nyata, bandingkan hasil dengan instance 18.0 |
| Kontrol fetch email lanjutan | AC-08 s/d AC-11 | Admin sistem verifikasi email fetch tetap berjalan sesuai konfigurasi `mark_read` yang sama seperti 18.0 |

## Ringkasan

| Step | Role | Tipe | Eksekusi | Jumlah AC |
|---|---|---|---|---|
| 9 | Developer | Unit/Integration (tidak ada Tour) | Otomatis/background — 23 test existing (21 reuse apa adanya, 2 wajib update) | 21 AC, 1 kondisional (AC-04-02) |
| 10 | QA | Manual/AI-interaktif/AI+tool eksternal | Campuran per skenario | 21 AC |
| 11 | PM/FA/User | UAT | Manual (selalu) | 2 kelompok fitur |
